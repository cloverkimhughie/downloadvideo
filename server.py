"""Single-user downloader. Run behind private Codespaces forwarding or on localhost."""
import json
import os
import re
import secrets
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parent
TOKEN = secrets.token_urlsafe(32)
JOBS = {}
LOCK = threading.RLock()
SLOT = threading.BoundedSemaphore(1)
TTL = 900
LIMIT = 250 * 1024 * 1024


def normalize_url(value):
    if not isinstance(value, str) or len(value) > 2048:
        raise ValueError('유튜브 영상 링크를 입력해 주세요.')
    u = urlsplit(value.strip())
    if u.scheme not in ('https', 'http') or u.username or u.password or u.port:
        raise ValueError('올바른 유튜브 링크를 입력해 주세요.')
    host = (u.hostname or '').lower()
    if host == 'youtu.be':
        video = u.path.strip('/')
    elif host in ('youtube.com', 'www.youtube.com', 'm.youtube.com', 'music.youtube.com'):
        if u.path == '/watch':
            video = parse_qs(u.query).get('v', [''])[0]
        elif re.fullmatch(r'/(shorts|live|embed)/[A-Za-z0-9_-]{11}/?', u.path):
            video = u.path.split('/')[2]
        else:
            video = ''
    else:
        video = ''
    if not re.fullmatch(r'[A-Za-z0-9_-]{11}', video):
        raise ValueError('개별 유튜브 영상 링크만 지원해요.')
    return 'https://www.youtube.com/watch?v=' + video


def work(job, url, quality):
    proc = None
    try:
        proc = subprocess.Popen(
            [sys.executable, str(ROOT / 'worker.py'), url, quality, job['folder']],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=(os.name == 'posix'))
        try:
            code = proc.wait(timeout=600)
        except subprocess.TimeoutExpired:
            if os.name == 'posix':
                os.killpg(proc.pid, signal.SIGKILL)
            else:
                proc.kill()
            proc.wait()
            raise ValueError('처리 시간이 10분을 넘었어요. 짧은 영상이나 낮은 화질로 시도해 주세요.')
        result = Path(job['folder']) / 'result.json'
        data = json.loads(result.read_text()) if result.exists() else {}
        if code or not data.get('ok'):
            raise ValueError(data.get('error', '다운로드 도구를 실행하지 못했어요. 설치 상태를 확인해 주세요.'))
        file = Path(job['folder']) / 'video.mp4'
        if not file.exists() or not 0 < file.stat().st_size <= LIMIT:
            raise ValueError('저장 가능한 파일 크기(250MB)를 넘었거나 파일이 비어 있어요.')
        with LOCK:
            job.update(state='ready', title=data['title'], size=file.stat().st_size, finished=time.time())
    except Exception as exc:
        with LOCK:
            job.update(state='error', error=str(exc) if isinstance(exc, ValueError) else '영상 처리 중 오류가 발생했어요.', finished=time.time())
        shutil.rmtree(job['folder'], ignore_errors=True)
    finally:
        SLOT.release()


def clean():
    while True:
        time.sleep(30)
        with LOCK:
            for key, job in list(JOBS.items()):
                if job.get('finished', float('inf')) + TTL < time.time():
                    shutil.rmtree(job['folder'], ignore_errors=True)
                    del JOBS[key]


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # Do not log video URLs or private download tokens.

    def reply(self, status, body, mime='application/json; charset=utf-8'):
        if not isinstance(body, bytes):
            body = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path in ('/', '/app.js', '/style.css', '/config.js'):
            name, mime = {'/config.js': ('config.js', 'text/javascript; charset=utf-8'), '/': ('index.html', 'text/html; charset=utf-8'), '/app.js': ('app.js', 'text/javascript; charset=utf-8'), '/style.css': ('style.css', 'text/css; charset=utf-8')}[path]
            return self.reply(200, (ROOT / name).read_bytes(), mime)
        if path == '/api/config':
            return self.reply(200, {'token': TOKEN})
        match = re.fullmatch(r'/api/jobs/([a-f0-9]{32})(/file)?', path)
        if not match:
            return self.reply(404, {'error': '페이지를 찾을 수 없어요.'})
        with LOCK:
            job = JOBS.get(match[1])
            if not job:
                return self.reply(404, {'error': '파일이 만료되었어요. 다시 다운로드해 주세요.'})
            if not match[2]:
                return self.reply(200, {k: v for k, v in job.items() if k != 'folder'})
            if job['state'] != 'ready':
                return self.reply(409, {'error': '아직 파일이 준비되지 않았어요.'})
            # Open under the lock so cleanup cannot remove it before streaming.
            stream = open(Path(job['folder']) / 'video.mp4', 'rb')
            size = job['size']
        with stream:
            self.send_response(200)
            self.send_header('Content-Type', 'video/mp4')
            self.send_header('Content-Disposition', 'attachment; filename="youtube-video.mp4"')
            self.send_header('Content-Length', str(size))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            try:
                shutil.copyfileobj(stream, self.wfile)
            except (BrokenPipeError, ConnectionResetError):
                pass

    def do_POST(self):
        if self.path != '/api/jobs':
            return self.reply(404, {'error': '잘못된 요청이에요.'})
        if self.headers.get('X-App-Token') != TOKEN:
            return self.reply(403, {'error': '화면을 새로고침한 뒤 시도해 주세요.'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 4096:
                raise ValueError('요청 크기가 올바르지 않아요.')
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError('잘못된 요청이에요.')
            url = normalize_url(data.get('url'))
            quality = data.get('quality', '720')
            if quality not in ('360', '720', '1080'):
                raise ValueError('화질을 다시 선택해 주세요.')
        except (ValueError, TypeError) as exc:
            return self.reply(400, {'error': str(exc)})
        if not SLOT.acquire(blocking=False):
            return self.reply(429, {'error': '다른 영상을 처리 중이에요. 완료 후 다시 시도해 주세요.'})
        with LOCK:
            if len(JOBS) >= 10:
                SLOT.release()
                return self.reply(429, {'error': '저장 공간을 정리 중이에요. 15분 뒤 다시 시도해 주세요.'})
            key = secrets.token_hex(16)
            job = {'state': 'working', 'folder': tempfile.mkdtemp(prefix='downloadvideo-')}
            JOBS[key] = job
        threading.Thread(target=work, args=(job, url, quality), daemon=True).start()
        self.reply(202, {'id': key})


if __name__ == '__main__':
    threading.Thread(target=clean, daemon=True).start()
    port = int(os.environ.get('PORT', '8000'))
    print(f'Open http://localhost:{port}', flush=True)
    ThreadingHTTPServer((os.environ.get('BIND', '127.0.0.1'), port), Handler).serve_forever()
