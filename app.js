const form = document.querySelector('#form');
const button = document.querySelector('#submit');
const statusBox = document.querySelector('#status');
const progress = document.querySelector('#progress');
const save = document.querySelector('#save');
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
async function api(url, options) {
  const response = await fetch(url, {cache: 'no-store', ...options});
  let data;
  try { data = await response.json(); } catch { throw new Error('서버 연결을 확인해 주세요. Codespaces가 실행 중이어야 해요.'); }
  if (!response.ok) throw new Error(data.error || '요청을 처리하지 못했어요.');
  return data;
}
form.addEventListener('submit', async event => {
  event.preventDefault();
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
        save.href = `/api/jobs/${id}/file`;
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
