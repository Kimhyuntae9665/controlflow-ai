'use strict';
const byId = id => document.getElementById(id);
const source = window.ITGC_SOURCE;
const api = window.ITGC;
const statusNames = { pass: '통과', exception: '예외', unknown: '미확인' };
const fields = ['employee_id', 'account_id', 'departure_at', 'revocation_at', 'account_status'];
for (const key of fields) {
  const field = source.fields[key], li = document.createElement('li');
  const label = document.createElement('span'), value = document.createElement('span');
  label.className = 'label'; label.textContent = field.label;
  value.className = 'value'; value.textContent = field.value;
  li.title = `1페이지 인용: ${field.quote}`; li.append(label, value); byId('evidence').append(li);
}
byId('departure').textContent = source.fields.departure_at.value;
function stampAfter(hours) {
  const base = new Date(source.fields.departure_at.value.replace(' ', 'T').replace(' KST', ':00+09:00'));
  return new Date(base.getTime() + hours * 3600000 + 9 * 3600000).toISOString().slice(0, 16).replace('T', ' ') + ' KST';
}
function render() {
  const input = { delayHours: byId('delay').value === '' ? NaN : byId('delay').value, limitHours: byId('limit').value === '' ? NaN : byId('limit').value, accountActive: byId('active').checked, evidenceMissing: byId('missing').checked };
  const result = api.evaluate(input);
  byId('error').hidden = result.valid;
  byId('error').textContent = result.valid ? '' : result.error;
  if (!result.valid) {
    byId('summary').textContent = '입력 오류 · 판정 보류'; byId('results').replaceChildren();
    byId('wait-value').textContent = '입력 확인 필요'; byId('deadline').textContent = '유효한 시간을 입력하세요.';
    byId('fill').style.width = '0%'; byId('wait-stage').className = 'stage unknown';
    byId('account-value').textContent = '계산 보류'; byId('revocation').textContent = '입력 오류'; byId('account-stage').className = 'stage unknown';
    byId('compare-delay').textContent = '오류'; byId('compare-account').textContent = '보류'; byId('compare-counts').textContent = '—';
    return;
  }
  const { delayHours: delay, limitHours: limit, accountActive: active, evidenceMissing: missing } = result.input;
  byId('delay-range').value = delay;
  byId('summary').textContent = `통과 ${result.counts.pass} · 예외 ${result.counts.exception} · 미확인 ${result.counts.unknown}`;
  byId('wait-value').textContent = missing ? '시각 확인 필요' : `${delay}시간 대기`;
  byId('fill').style.width = `${delay / 72 * 100}%`;
  byId('fill').style.background = missing ? '#a7843a' : delay > limit ? '#b34e3a' : '#006d68';
  byId('deadline').textContent = missing ? `가정 입력 ${delay}시간 · 증빙 없음` : `허용 ${limit}시간 / ${delay <= limit ? '기한 이내' : '기한 초과'}`;
  byId('wait-stage').className = `stage wait ${result.checks[1].status}`;
  byId('account-value').textContent = active ? '활성 유지' : '비활성 확인';
  byId('account-stage').className = `stage ${result.checks[0].status}`;
  byId('revocation').textContent = missing ? '회수 시각 미확인' : `가정 시각 ${stampAfter(delay)}`;
  byId('results').replaceChildren();
  for (const check of result.checks) {
    const card = document.createElement('div'); card.className = `result ${check.status}`;
    const top = document.createElement('div'); top.className = 'top';
    const id = document.createElement('span'); id.className = 'id'; id.textContent = check.id;
    const status = document.createElement('span'); status.className = 'status'; status.textContent = statusNames[check.status];
    const title = document.createElement('h3'); title.textContent = check.title;
    const reason = document.createElement('p'); reason.textContent = check.reason;
    top.append(id, status); card.append(top, title, reason); byId('results').append(card);
  }
  byId('compare-delay').textContent = missing ? `${delay}시간 (가정)` : `${delay}시간`;
  byId('compare-account').textContent = active ? '활성' : '비활성';
  byId('compare-counts').textContent = `${result.counts.pass} / ${result.counts.exception} / ${result.counts.unknown}`;
}
function preset(value) {
  byId('delay').value = value.delayHours; byId('delay-range').value = value.delayHours;
  byId('limit').value = value.limitHours; byId('active').checked = value.accountActive; byId('missing').checked = value.evidenceMissing;
  render();
}
for (const id of ['delay', 'limit', 'active', 'missing']) byId(id).addEventListener('input', render);
byId('delay-range').addEventListener('input', () => { byId('delay').value = byId('delay-range').value; render(); });
byId('baseline').addEventListener('click', () => preset(api.reset()));
byId('reset').addEventListener('click', () => preset(api.reset()));
byId('late').addEventListener('click', () => preset({ ...api.reset(), delayHours: 48, accountActive: true }));
preset(source.baseline);
