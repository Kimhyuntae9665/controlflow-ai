(function (root) {
  'use strict';
  const baseline = Object.freeze({ delayHours: 12, limitHours: 24, accountActive: false, evidenceMissing: false });
  function evaluate(input) {
    const delay = Number(input.delayHours), limit = Number(input.limitHours);
    if (!Number.isFinite(delay) || delay < 0 || delay > 72) return { valid: false, error: '회수 지연은 0~72시간의 숫자로 입력하세요.' };
    if (!Number.isFinite(limit) || limit < 0 || limit > 72) return { valid: false, error: '허용시간은 0~72시간의 숫자로 입력하세요.' };
    const i01 = { id: 'I01', title: '계정 비활성화', status: input.accountActive ? 'exception' : 'pass', reason: input.accountActive ? '퇴사자 계정이 활성 상태입니다.' : '계정이 비활성 상태입니다.' };
    const i02 = { id: 'I02', title: '회수 기한 준수', status: input.evidenceMissing ? 'unknown' : (delay <= limit ? 'pass' : 'exception'), reason: input.evidenceMissing ? '시각 증빙이 없어 지연시간을 확정할 수 없습니다.' : `${delay}시간 ${delay <= limit ? '≤' : '>'} 허용 ${limit}시간` };
    const checks = [i01, i02];
    return { valid: true, input: { delayHours: delay, limitHours: limit, accountActive: !!input.accountActive, evidenceMissing: !!input.evidenceMissing }, checks, counts: { pass: checks.filter(c => c.status === 'pass').length, exception: checks.filter(c => c.status === 'exception').length, unknown: checks.filter(c => c.status === 'unknown').length } };
  }
  const api = { baseline, evaluate, reset: () => ({ ...baseline }) };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.ITGC = api;
})(typeof window !== 'undefined' ? window : globalThis);
