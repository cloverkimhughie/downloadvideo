# downloadvideo

유튜브 링크를 넣고 MP4 파일을 저장하는 개인용 웹 앱입니다. 360p / 720p / 1080p 최대 화질을 선택할 수 있으며, 선택한 값 이하의 사용 가능한 H.264 영상과 소리를 다운로드합니다.

## 아이패드에서도 실행하기: GitHub Codespaces

1. 이 저장소에서 **Code → Codespaces → Create codespace on main**을 선택합니다.
2. 최초 환경 설치가 끝날 때까지 기다립니다. Python, Node.js, FFmpeg, yt-dlp가 준비됩니다.
3. 아래쪽 터미널에서 `python server.py`를 실행합니다.
4. **Ports** 탭의 **8000** 포트에서 **Open in Browser**를 누릅니다. 포트 공개 범위는 **Private**로 유지하세요.
5. 유튜브 링크 → 화질 선택 → **영상 준비하기** → **MP4 파일 저장하기** 순서로 사용합니다.
6. 아이패드에서는 브라우저의 다운로드 목록 또는 파일 앱에서 저장된 파일을 확인합니다. 미리보기가 열리면 공유 메뉴의 ‘파일에 저장’을 사용할 수 있습니다.

Codespace가 실행되는 동안 사용할 수 있습니다. 사용이 끝나면 Codespace를 중지하세요. Codespaces에는 계정별 사용량 제한이 있으며 계정의 요금·사용량 설정을 확인하세요. 이 저장소에는 상시 공개 서버가 배포되어 있지 않습니다.

**GitHub Pages만으로는 작동하지 않습니다.** Python 다운로드 서버가 필요합니다. `index.html`을 직접 여는 대신 위 서버 주소를 사용하세요.

## 내 컴퓨터에서 실행하기

Python 3.10 이상, Node.js 22 이상, FFmpeg/ffprobe를 설치하고 PATH에서 실행 가능하게 준비합니다.

```sh
python -m pip install -U -r requirements.txt
python server.py
```

브라우저에서 http://localhost:8000 을 엽니다. 기본적으로 localhost에서만 연결을 받습니다. 이 서버는 개인용이며 공개 서비스용 인증·사용자별 할당량 기능은 포함하지 않습니다.

## 동작 및 제한

- 공개된 개별 영상 / Shorts 링크 지원. 재생목록 링크는 지원하지 않으며 영상 링크에 포함된 재생목록 매개변수는 제거합니다.
- 최대 30분, 최종 파일 250MiB, 동시에 1건 처리, 작업당 10분 제한.
- 브라우저에서 상태를 주기적으로 확인하므로 긴 다운로드도 단일 HTTP 요청에 의존하지 않습니다.
- 완료 파일은 약 15분 후 자동 삭제합니다. 최대 10개 작업만 보관합니다.
- 직접 만든 영상이나 다운로드 허락을 받은 영상에 사용하세요.
- 로그인 필요 영상, 연령 제한 영상, 진행 중인 라이브는 지원하지 않습니다. 쿠키 가져오기나 제한 우회 기능은 없습니다.
- YouTube 변경, 서버 IP 차단, 제공 화질 또는 코덱에 따라 실패할 수 있습니다. 특히 클라우드 서버는 YouTube의 요청 차단 영향을 받을 수 있습니다.
- 화질은 원본보다 높일 수 없습니다. 실패하면 더 낮은 화질 또는 다른 허용된 영상으로 확인하세요.
- yt-dlp 업데이트: `python -m pip install -U -r requirements.txt`
- 비정상 강제 종료 시 임시 폴더가 남을 수 있습니다. 실행 중인 작업이 없는 상태에서 시스템 임시 디렉터리의 `downloadvideo-` 폴더를 정리할 수 있습니다.

## 검증

```sh
python -m unittest discover -s tests -v
```

URL 검증, 요청 보호, 작업 상태, MP4 응답, 실패 처리 및 제한을 로컬 모의 다운로드로 검사합니다. 실제 YouTube 영상 다운로드 성공을 보장하는 테스트는 아닙니다.

참고: [yt-dlp 공식 문서](https://github.com/yt-dlp/yt-dlp), [GitHub Pages 소개](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)
