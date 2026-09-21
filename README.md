# downloadvideo

유튜브 링크를 넣고 MP4 파일을 저장하는 개인용 웹 앱입니다. 360p / 720p / 1080p 최대 화질을 선택할 수 있으며, 선택한 값 이하의 사용 가능한 H.264 영상과 소리를 다운로드합니다.

## GitHub Pages 주소에서 열기

목표 주소: https://cloverkimhughie.github.io/downloadvideo/

화면 파일은 프로젝트 하위 경로를 지원합니다. 저장소 **Settings → Pages → Deploy from a branch → main → /(root) → Save**로 게시할 수 있습니다.

현재 이 저장소에는 별도 운영 서버 주소가 설정되어 있지 않습니다. Pages 화면에서는 **다운로드 서비스 준비 중**으로 표시되며 다운로드 버튼이 비활성화됩니다. Pages 자체는 Python을 실행하지 않으므로, 화면 게시만으로 다운로드 기능이 활성화되지 않습니다.

### 운영 서버 연결에 남은 작업

1. Python, FFmpeg 및 Node.js를 지원하는 HTTPS 서버를 준비합니다.
2. 운영 서버에 인증과 이용량 제한을 적용합니다. 기존 server.py는 개인용 서버이므로 그대로 공개하지 않습니다.
3. 운영 서버에 Pages 출처 `https://cloverkimhughie.github.io`를 허용하는 CORS 응답과 OPTIONS 처리를 추가합니다. API의 GET/POST 및 X-App-Token 요청 헤더를 지원해야 합니다.
4. `config.js`의 `apiBaseUrl`에 운영 서버의 HTTPS 기본 주소를 입력합니다. 이 파일은 공개되므로 비밀번호·쿠키·비밀 키를 넣지 않습니다.
5. 실제 허용된 공개 영상의 정보 조회, 다운로드, 파일 전달을 운영 서버에서 확인합니다.

현재 Codespaces에서 확인된 YouTube의 봇 확인 요구는 Pages로 화면을 옮겨도 해결되지 않습니다. 사설 Codespaces 포트는 GitHub 인증을 요구하므로 Pages의 외부 API로 바로 연결할 수 있다고 가정하지 않습니다. 정상 동작하는 백엔드를 확인한 뒤 연결해야 합니다.

## 개인용 실행: GitHub Codespaces

1. 이 저장소에서 **Code → Codespaces → Create codespace on main**을 선택합니다.
2. 최초 환경 설치가 끝날 때까지 기다립니다. Python, Node.js, FFmpeg, yt-dlp가 준비됩니다.
3. 아래쪽 터미널에서 `python server.py`를 실행합니다.
4. **Ports** 탭의 **8000** 포트에서 **Open in Browser**를 누릅니다. 포트 공개 범위는 **Private**로 유지하세요.
5. 유튜브 링크 → 화질 선택 → **영상 준비하기** → **MP4 파일 저장하기** 순서로 사용합니다.
6. 아이패드에서는 브라우저의 다운로드 목록 또는 파일 앱에서 저장된 파일을 확인합니다. 미리보기가 열리면 공유 메뉴의 ‘파일에 저장’을 사용할 수 있습니다.

Codespace가 실행되는 동안 사용할 수 있습니다. 사용이 끝나면 Codespace를 중지하세요. Codespaces에는 계정별 사용량 제한이 있으며 계정의 요금·사용량 설정을 확인하세요. 이 저장소에는 상시 공개 서버가 배포되어 있지 않습니다.

GitHub Pages에는 화면을 게시할 수 있지만 실제 다운로드에는 Python 서버가 필요합니다. 개인용 실행에서는 위 서버 주소를 사용하세요.

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
