"""Isolated download process. No cookies, accounts, or access-restriction bypass."""
import json
import sys
from pathlib import Path

LIMIT = 250 * 1024 * 1024


def restriction(info):
    if (info.get('age_limit') or 0) >= 18:
        return '연령 제한 영상은 지원하지 않아요.'
    if info.get('is_live') or info.get('live_status') in ('is_live', 'is_upcoming'):
        return '진행 중인 라이브 방송은 지원하지 않아요.'
    if not info.get('duration') or info['duration'] > 1800:
        return '길이를 확인할 수 없거나 30분을 넘는 영상은 지원하지 않아요.'
    if info.get('availability') in ('private', 'premium_only', 'subscriber_only', 'needs_auth'):
        return '로그인이 필요한 영상은 지원하지 않아요.'
    return None


def download(url, quality, folder):
    from yt_dlp import YoutubeDL
    from yt_dlp.utils import DownloadError

    def guard(info, *, incomplete=False):
        return None if incomplete else restriction(info)

    def progress(data):
        total = sum(p.stat().st_size for p in folder.iterdir() if p.is_file())
        if total > LIMIT:
            raise DownloadError('파일 크기 제한을 넘었어요. 낮은 화질로 시도해 주세요.')

    options = {
        'quiet': True, 'no_warnings': True, 'noplaylist': True,
        'socket_timeout': 20, 'retries': 2, 'fragment_retries': 2,
        'cachedir': False, 'age_limit': 17,
        'js_runtimes': {'node': {}},
        'outtmpl': str(folder / 'video.%(ext)s'),
        'format': f'bv[vcodec^=avc1][height<={quality}]+ba[ext=m4a]/b[ext=mp4][vcodec^=avc1][height<={quality}]',
        'merge_output_format': 'mp4', 'max_filesize': LIMIT,
        'match_filter': guard, 'progress_hooks': [progress],
    }
    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=False)
        if not info:
            raise ValueError('지원하지 않는 영상이에요. 공개된 30분 이하 영상을 확인해 주세요.')
        reason = restriction(info)
        if reason:
            raise ValueError(reason)
        ydl.process_info(info)
        return {'ok': True, 'title': info.get('title', 'YouTube 영상')}


if __name__ == '__main__':
    folder = Path(sys.argv[3])
    try:
        result = download(sys.argv[1], sys.argv[2], folder)
    except ValueError as exc:
        result = {'ok': False, 'error': str(exc)}
    except Exception:
        result = {'ok': False, 'error': '영상을 가져오지 못했어요. 공개 여부·선택 화질을 확인해 주세요. YouTube가 서버의 요청을 차단한 경우에도 실패할 수 있어요.'}
    (folder / 'result.json').write_text(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if result['ok'] else 1)
