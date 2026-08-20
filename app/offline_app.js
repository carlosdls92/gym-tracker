// PLAN_SLUG y DAY_TOTALS se inyectan desde Python antes de este bloque
let currentDay = 0, openDetail = null;

function gp(d) {
  try { const r = localStorage.getItem('gym-p-' + PLAN_SLUG + '-' + d); return r ? new Set(JSON.parse(r)) : new Set(); }
  catch { return new Set(); }
}
function sp(d, s) {
  try { localStorage.setItem('gym-p-' + PLAN_SLUG + '-' + d, JSON.stringify([...s])); } catch {}
}
function up(d) {
  const done = gp(d), total = DAY_TOTALS[d] || 1, n = done.size;
  const bar = document.getElementById('pb-' + d);
  const cnt = document.getElementById('cnt-' + d);
  const ban = document.getElementById('ban-' + d);
  if (bar) bar.style.width = (n / total * 100) + '%';
  if (cnt) cnt.textContent = n + ' / ' + total;
  if (ban) ban.classList.toggle('show', n === total && total > 0);
}
function toggleItem(e, cid, day) {
  const btn = document.getElementById('chk-' + cid);
  if (!btn) return;
  if (e.target === btn || btn.contains(e.target)) {
    e.stopPropagation();
    const card = document.getElementById('card-' + cid);
    const done = card.classList.toggle('done');
    btn.style.cssText = done ? 'color:white;background:#4a9a4a;border-color:#4a9a4a' : '';
    const exId = cid.slice(cid.indexOf('-') + 1);
    const s = gp(day); done ? s.add(exId) : s.delete(exId); sp(day, s); up(day);
    if (done) { card.classList.add('just-done'); setTimeout(() => card.classList.remove('just-done'), 300); }
    return;
  }
  const det = document.getElementById('det-' + cid);
  if (!det) return;
  if (openDetail && openDetail !== det) openDetail.classList.remove('open');
  det.classList.toggle('open');
  openDetail = det.classList.contains('open') ? det : null;
}
function loadDay(n) {
  if (currentDay === n) return;
  if (openDetail) { openDetail.classList.remove('open'); openDetail = null; }
  if (currentDay) { const c = document.getElementById('day-' + currentDay); if (c) c.hidden = true; }
  currentDay = n;
  const dayEl = document.getElementById('day-' + n);
  dayEl.hidden = false;
  document.querySelectorAll('.tab[data-day]').forEach(t => t.classList.toggle('on', +t.dataset.day === n));
  try { localStorage.setItem('gym-last-plan', PLAN_SLUG); localStorage.setItem('gym-last-day', String(n)); } catch {}
}
(function () {
  // Restaurar estado de progreso en todos los días
  Object.keys(DAY_TOTALS).forEach(function (d) {
    const day = +d, done = gp(day);
    done.forEach(function (exId) {
      const cid = day + '-' + exId;
      const card = document.getElementById('card-' + cid);
      const btn  = document.getElementById('chk-' + cid);
      if (card) card.classList.add('done');
      if (btn)  btn.style.cssText = 'color:white;background:#4a9a4a;border-color:#4a9a4a';
    });
    up(day);
  });
  // Cargar último día o el primero
  let start = +Object.keys(DAY_TOTALS)[0];
  try {
    const lp = localStorage.getItem('gym-last-plan');
    const ld = +localStorage.getItem('gym-last-day');
    if (lp === PLAN_SLUG && ld && DAY_TOTALS[ld] !== undefined) start = ld;
  } catch {}
  loadDay(start);
})();
