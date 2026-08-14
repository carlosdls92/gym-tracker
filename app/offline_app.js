let currentDay = 0, currentTotal = 0, openDetail = null;

function gp(d) {
  try { const r = localStorage.getItem('gym-p-' + PLAN_SLUG + '-' + d); return r ? new Set(JSON.parse(r)) : new Set(); }
  catch { return new Set(); }
}
function sp(d, s) {
  try { localStorage.setItem('gym-p-' + PLAN_SLUG + '-' + d, JSON.stringify([...s])); } catch {}
}
function up() {
  const n = gp(currentDay).size;
  const bar = document.getElementById('progressBar');
  const cnt = document.getElementById('countDisplay');
  const ban = document.getElementById('completeBanner');
  if (bar) bar.style.width = (n / currentTotal * 100) + '%';
  if (cnt) cnt.textContent = n + ' / ' + currentTotal;
  if (ban) ban.classList.toggle('show', currentTotal > 0 && n === currentTotal);
}
function toggleItem(e, id) {
  const btn = document.getElementById('chk-' + id);
  if (!btn) return;
  if (e.target === btn || btn.contains(e.target)) {
    e.stopPropagation();
    const card = document.getElementById('card-' + id);
    const done = card.classList.toggle('done');
    btn.style.cssText = done ? 'color:white;background:#4a9a4a;border-color:#4a9a4a' : '';
    const s = gp(currentDay); done ? s.add(id) : s.delete(id); sp(currentDay, s); up();
    if (done) { card.classList.add('just-done'); setTimeout(() => card.classList.remove('just-done'), 300); }
    return;
  }
  const det = document.getElementById('det-' + id);
  if (!det) return;
  if (openDetail && openDetail !== det) openDetail.classList.remove('open');
  det.classList.toggle('open');
  openDetail = det.classList.contains('open') ? det : null;
}
function gs(id, i) { return GIFS[id + '/' + i] || ''; }
function ck(d) { return d ? ' style="color:white;background:#4a9a4a;border-color:#4a9a4a"' : ''; }
function dots(n) { return Array.from({ length: n || 4 }, () => '<div class="set-dot"></div>').join(''); }

function cardioCard(ex, done) {
  const dc = done ? ' done' : '', g0 = ex.gifs[0] || {}, g1 = ex.gifs[1] || {};
  return `<div class="card${dc}" id="card-${ex._id}" onclick="toggleItem(event,'${ex._id}')">
<div class="card-imgs">
  <div class="card-img"><img src="${gs(ex._id, 0)}" loading="lazy" alt="Cardio"><span class="img-tag accent">${g0.label || ''}</span></div>
  <div class="card-img"><img src="${gs(ex._id, 1)}" loading="lazy" alt="Cardio"><span class="img-tag accent">${g1.label || ''}</span></div>
</div>
<div class="cardio-info">
  <div class="cardio-text"><div class="cardio-name">Cardio</div><div class="cardio-meta">${ex.meta || ''}</div></div>
  <div class="cardio-time">${ex.duration || ''}</div>
  <div class="check-btn" id="chk-${ex._id}"${ck(done)}>✓</div>
</div></div>`;
}

function exCard(ex, done) {
  const dc = done ? ' done' : '', g0 = ex.gifs[0] || {}, g1 = ex.gifs[1] || {};
  const tags = (ex.tags || []).map(t => `<span class="detail-tag">${t}</span>`).join('');
  const sets = ex.sets || 4, reps = ex.reps || '12';
  return `<div class="card${dc}" id="card-${ex._id}" onclick="toggleItem(event,'${ex._id}')">
<div class="card-imgs">
  <div class="card-img"><img src="${gs(ex._id, 0)}" loading="lazy" alt="${ex.name}"><span class="img-tag">${g0.label || ''}</span></div>
  <div class="card-img"><img src="${gs(ex._id, 1)}" loading="lazy" alt="${ex.name}"><span class="img-tag${g1.accent ? ' accent' : ''}">${g1.label || ''}</span></div>
</div>
<div class="card-info">
  <div class="card-text">
    <div class="card-name">${ex.name}</div>
    <div class="card-sub"><span class="muscle-badge">${ex.muscle_badge || ''}</span><span class="expand-hint">↓ técnica</span></div>
  </div>
  <div class="card-right">
    <div class="sets-row">${dots(sets)}</div>
    <div class="reps-label">${sets}×${reps}</div>
    <div class="check-btn" id="chk-${ex._id}"${ck(done)}>✓</div>
  </div>
</div>
<div class="card-detail" id="det-${ex._id}">
  <div class="detail-body"><div class="detail-text">${ex.technique || ''}</div><div class="detail-tags">${tags}</div></div>
</div></div>`;
}

function renderDay(data) {
  currentTotal = data.total;
  const done = gp(currentDay), n = done.size;
  const tp = data.title.split(' ');
  const th = tp.length >= 2 ? tp[0] + '<br>' + tp.slice(1).join(' ') : data.title;
  const mt = (data.muscle_tags || []).map(t => `<span class="tag">${t}</span>`).join('');
  let h = `<header data-day="${data.day_num}">
<div class="label-day">Gym CAR — Nacho</div><h1>${th}</h1>
<div class="subtitle">${data.subtitle}</div>
<div class="muscle-tags">${mt}</div>
</header>
<div class="progress-wrap">
<div class="progress-header"><span class="progress-label">Progreso</span><span class="progress-count" id="countDisplay">${n} / ${data.total}</span></div>
<div class="progress-bar-bg"><div class="progress-bar-fill" id="progressBar" style="width:${n / data.total * 100}%"></div></div>
</div>
<div class="content"><div style="height:18px"></div>`;
  let shown = false;
  for (const ex of data.exercises) {
    const d = done.has(ex._id);
    if (ex.type === 'cardio') { h += cardioCard(ex, d); h += '<div class="section-title">Ejercicios</div>'; shown = true; }
    else { if (!shown) { h += '<div class="section-title">Ejercicios</div>'; shown = true; } h += exCard(ex, d); }
  }
  h += `<div class="complete-banner${n === data.total && data.total > 0 ? ' show' : ''}" id="completeBanner">
<div class="complete-emoji">🔥</div><div class="complete-title">SESIÓN COMPLETADA</div>
<div class="complete-sub">${data.title} terminado · Buen trabajo</div>
</div><div class="footer">GYM CAR · Nacho</div></div>`;
  document.getElementById('root').innerHTML = h;
  openDetail = null;
}

function loadDay(n) {
  if (currentDay === n) return;
  currentDay = n; openDetail = null;
  document.querySelectorAll('.tab[data-day]').forEach(t => t.classList.toggle('on', +t.dataset.day === n));
  const data = DAYS.find(d => d.day_num === n);
  if (data) {
    renderDay(data);
    try { localStorage.setItem('gym-last-plan', PLAN_SLUG); localStorage.setItem('gym-last-day', String(n)); } catch {}
  }
}

(function () {
  const tb = document.getElementById('tabs-bar');
  tb.innerHTML = DAYS.map(d =>
    `<button class="tab" data-day="${d.day_num}" onclick="loadDay(${d.day_num})">${d.day_label}</button>`
  ).join('');
  let start = DAYS[0].day_num;
  try {
    const lp = localStorage.getItem('gym-last-plan');
    const ld = +localStorage.getItem('gym-last-day');
    if (lp === PLAN_SLUG && ld && DAYS.find(d => d.day_num === ld)) start = ld;
  } catch {}
  loadDay(start);
})();
