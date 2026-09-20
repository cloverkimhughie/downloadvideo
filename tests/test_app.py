import http.client
import json
import shutil
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
import server
from worker import restriction

class Tests(unittest.TestCase):
    def test_urls(self):
        for url in ('https://youtu.be/abcdefghijk?t=2', 'https://www.youtube.com/watch?v=abcdefghijk&list=x', 'https://m.youtube.com/shorts/abcdefghijk'):
            self.assertEqual(server.normalize_url(url), 'https://www.youtube.com/watch?v=abcdefghijk')
        for url in ('https://youtube.com.evil.test/watch?v=abcdefghijk', 'http://127.0.0.1/', 'https://youtube.com@evil.test/', 'file:///etc/passwd', 'https://youtube.com/playlist?list=x', None):
            with self.subTest(url=url), self.assertRaises(ValueError):
                server.normalize_url(url)

    def test_restrictions(self):
        self.assertIsNone(restriction({'duration': 120, 'age_limit': 0}))
        for info in ({'duration': 1801}, {'duration': 2, 'age_limit': 18}, {'duration': 2, 'is_live': True}, {'duration': 2, 'availability': 'needs_auth'}, {}):
            self.assertIsNotNone(restriction(info))

    def test_worker_results(self):
        for success in (True, False):
            with tempfile.TemporaryDirectory() as folder:
                job = {'state': 'working', 'folder': folder}
                if success:
                    (Path(folder) / 'video.mp4').write_bytes(b'mock')
                    (Path(folder) / 'result.json').write_text(json.dumps({'ok': True, 'title': 'Test'}))
                server.SLOT.acquire()
                with patch('server.subprocess.Popen') as process:
                    process.return_value.wait.return_value = 0 if success else 1
                    server.work(job, 'https://www.youtube.com/watch?v=abcdefghijk', '720')
                self.assertEqual(job['state'], 'ready' if success else 'error')
                self.assertTrue(server.SLOT.acquire(blocking=False))
                server.SLOT.release()

class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = server.ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def request(self, method, path, data=None, token=True):
        connection = http.client.HTTPConnection('127.0.0.1', self.httpd.server_port)
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['X-App-Token'] = server.TOKEN
        connection.request(method, path, json.dumps(data) if data is not None else None, headers)
        response = connection.getresponse()
        result = (response.status, dict(response.getheaders()), response.read())
        connection.close()
        return result

    def test_page(self):
        self.assertEqual(self.request('GET', '/')[0], 200)
        self.assertEqual(self.request('GET', '/server.py')[0], 404)

    def test_invalid_requests(self):
        payload = {'url': 'https://youtu.be/abcdefghijk', 'quality': '720'}
        self.assertEqual(self.request('POST', '/api/jobs', payload, token=False)[0], 403)
        self.assertEqual(self.request('POST', '/api/jobs', {**payload, 'quality': '999'})[0], 400)
        self.assertEqual(self.request('POST', '/api/jobs', [1, 2])[0], 400)

    def test_busy(self):
        server.SLOT.acquire()
        try:
            self.assertEqual(self.request('POST', '/api/jobs', {'url': 'https://youtu.be/abcdefghijk'})[0], 429)
        finally:
            server.SLOT.release()

    def test_download(self):
        key = 'a' * 32
        with tempfile.TemporaryDirectory() as folder:
            content = b'fake-mp4-for-http-test'
            (Path(folder) / 'video.mp4').write_bytes(content)
            server.JOBS[key] = {'state': 'ready', 'folder': folder, 'size': len(content), 'title': 'Test'}
            try:
                status, _, body = self.request('GET', '/api/jobs/' + key)
                self.assertEqual(status, 200)
                self.assertNotIn('folder', json.loads(body))
                status, headers, body = self.request('GET', '/api/jobs/' + key + '/file')
                self.assertEqual(status, 200)
                self.assertEqual(body, content)
                self.assertIn('attachment', headers['Content-Disposition'])
                self.assertEqual(self.request('GET', '/api/jobs/' + 'b' * 32)[0], 404)
            finally:
                del server.JOBS[key]
