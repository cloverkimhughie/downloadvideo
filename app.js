const form = document.querySelector('#form');
const button = document.querySelector('#submit');
const statusBox = document.querySelector('#status');
const progress = document.querySelector('#progress');
const save = document.querySelector('#save');
const isPages = location.hostname.endsWith('.github.io');
let apiBase = '';
let available = false;
const endpoint = path => apiBase + path;
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
async function api(url, options) {
  const response = await fetch(endpoint(url), {cache: 'no-store', ...options, signal: AbortSignal.timeout(15000)});
  let data;
  try { data = await response.json(); } catch { throw new Error('다운로드 서비스에 연결할 수 없어요. 잠시 후 새로고침해 주세요.'); }
  if (!response.ok) throw new Error(data.error || '요청을 처리하지 못했어요.');
  return data;
}
form.addEventListener('submit', async event => {
  event.preventDefault();
  if (!available) return;
  button.disabled = true;
  save.hidden = true;
  progress.hidden = false;
  statusBox.className = '';
  statusBox.textContent = '영상을 확인하고 준비하고 있어요. 이 화면을 열어 두세요.';
  try {
    const {token} = await api('/api/config');
    const {id} = await api('/api/jobs', {method: 'POST', headers: {'Content-Type': 'application/json', 'X-App-Token': token}, body: JSON.stringify({url: document.querySelector('#url').value.trim(), quality: document.querySelector('#quality').value})});
    const deadline = Date.now() + 660000;
    while (Date.now() < deadline) {
      await delay(1800);
      const job = await api(`/api/jobs/${id}`);
      if (job.state === 'error') throw new Error(job.error);
      if (job.state === 'ready') {
        statusBox.textContent = `${job.title} · ${(job.size / 1024 / 1024).toFixed(1)}MB — 저장할 준비가 되었어요!`;
        save.href = endpoint(`/api/jobs/${id}/file`);
        save.hidden = false;
        return;
      }
    }
    throw new Error('응답 시간이 길어지고 있어요. 잠시 후 다시 시도해 주세요.');
  } catch (error) {
    statusBox.textContent = error.message || '연결에 실패했어요. 다시 시도해 주세요.';
    statusBox.className = 'error';
  } finally {
    button.disabled = false;
    progress.hidden = true;
  }
});

async function initialize() {
  try {
    const configured = window.DOWNLOADVIDEO_CONFIG?.apiBaseUrl?.trim() || '';
    if (!configured && isPages) {
      statusBox.textContent = '다운로드 서비스 준비 중이에요. 연결이 완료되면 여기에서 영상을 저장할 수 있어요.';
      button.textContent = '다운로드 서비스 준비 중';
      return;
    }
    if (configured) {
      const target = new URL(configured);
      if (target.protocol !== 'https:' || target.username || target.password || target.search || target.hash) {
        throw new Error('다운로드 서비스 주소 설정을 확인해야 해요.');
      }
      apiBase = target.href.replace(/\/$/, '');
    }
    const config = await api('/api/config');
    if (typeof config.token !== 'string' || !config.token) throw new Error('다운로드 서비스 응답을 확인할 수 없어요.');
    available = true;
    button.disabled = false;
    statusBox.textContent = '링크를 입력하면 시작할 수 있어요.';
  } catch (error) {
    statusBox.textContent = '다운로드 서비스에 연결할 수 없어요. 잠시 후 새로고침해 주세요.';
    statusBox.className = 'error';
    button.textContent = '연결 대기 중';
  }
}
initialize();
