let currentDay = 0;
let currentTotal = 0;
let openDetail = null;

// ── Progress (localStorage) ───────────────────────────────────────────────────
function getProgress(day) {
  try {
    const raw = localStorage.getItem('gym-p-' + day);
    return raw ? new Set(JSON.parse(raw)) : new Set();
  } catch { return new Set(); }
}
function saveProgress(day, done) {
  try { localStorage.setItem('gym-p-' + day, JSON.stringify([...done])); } catch {}
}

function updateProgress() {
  const n = getProgress(currentDay).size;
  const bar    = document.getElementById('progressBar');
  const count  = document.getElementById('countDisplay');
  const banner = document.getElementById('completeBanner');
  if (bar)    bar.style.width = (n / currentTotal * 100) + '%';
  if (count)  count.textContent = n + ' / ' + currentTotal;
  if (banner) banner.classList.toggle('show', n === currentTotal);
}

// ── Toggle item ───────────────────────────────────────────────────────────────
function toggleItem(e, id) {
  const btn = document.getElementById('chk-' + id);
  if (!btn) return;

  if (e.target === btn || btn.contains(e.target)) {
    e.stopPropagation();
    const card   = document.getElementById('card-' + id);
    const isDone = card.classList.toggle('done');
    btn.style.cssText = isDone ? 'color:white;background:#4a9a4a;border-color:#4a9a4a' : '';
    const done = getProgress(currentDay);
    isDone ? done.add(id) : done.delete(id);
    saveProgress(currentDay, done);
    updateProgress();
    if (isDone) {
      card.classList.add('just-done');
      setTimeout(() => card.classList.remove('just-done'), 300);
    }
    return;
  }

  // toggle technique panel (only regular cards have it)
  const detail = document.getElementById('det-' + id);
  if (!detail) return;
  if (openDetail && openDetail !== detail) openDetail.classList.remove('open');
  detail.classList.toggle('open');
  openDetail = detail.classList.contains('open') ? detail : null;
}

// ── Card builders ─────────────────────────────────────────────────────────────
function chkStyle(isDone) {
  return isDone ? ' style="color:white;background:#4a9a4a;border-color:#4a9a4a"' : '';
}

function buildCardioCard(ex, isDone) {
  const dc = isDone ? ' done' : '';
  const g0 = ex.gifs[0] || {};
  const g1 = ex.gifs[1] || {};
  return `<div class="card${dc}" id="card-${ex._id}" onclick="toggleItem(event,'${ex._id}')">
  <div class="card-imgs">
    <div class="card-img">
      <img src="/api/gif/${ex._id}/0" loading="lazy" alt="Cardio">
      <span class="img-tag accent">${g0.label || ''}</span>
    </div>
    <div class="card-img">
      <img src="/api/gif/${ex._id}/1" loading="lazy" alt="Cardio">
      <span class="img-tag accent">${g1.label || ''}</span>
    </div>
  </div>
  <div class="cardio-info">
    <div class="cardio-text">
      <div class="cardio-name">Cardio</div>
      <div class="cardio-meta">${ex.meta || ''}</div>
    </div>
    <div class="cardio-time">${ex.duration || ''}</div>
    <div class="check-btn" id="chk-${ex._id}"${chkStyle(isDone)}>✓</div>
  </div>
</div>`;
}

function buildExCard(ex, isDone) {
  const dc = isDone ? ' done' : '';
  const g0 = ex.gifs[0] || {};
  const g1 = ex.gifs[1] || {};
  const tags = (ex.tags || []).map(t => `<span class="detail-tag">${t}</span>`).join('');
  return `<div class="card${dc}" id="card-${ex._id}" onclick="toggleItem(event,'${ex._id}')">
  <div class="card-imgs">
    <div class="card-img">
      <img src="/api/gif/${ex._id}/0" loading="lazy" alt="${ex.name}">
      <span class="img-tag">${g0.label || ''}</span>
    </div>
    <div class="card-img">
      <img src="/api/gif/${ex._id}/1" loading="lazy" alt="${ex.name}">
      <span class="img-tag${g1.accent ? ' accent' : ''}">${g1.label || ''}</span>
    </div>
  </div>
  <div class="card-info">
    <div class="card-text">
      <div class="card-name">${ex.name}</div>
      <div class="card-sub">
        <span class="muscle-badge">${ex.muscle_badge || ''}</span>
        <span class="expand-hint">↓ técnica</span>
      </div>
    </div>
    <div class="card-right">
      <div class="sets-row">
        <div class="set-dot"></div><div class="set-dot"></div>
        <div class="set-dot"></div><div class="set-dot"></div>
      </div>
      <div class="reps-label">4×12</div>
      <div class="check-btn" id="chk-${ex._id}"${chkStyle(isDone)}>✓</div>
    </div>
  </div>
  <div class="card-detail" id="det-${ex._id}">
    <div class="detail-body">
      <div class="detail-text">${ex.technique || ''}</div>
      <div class="detail-tags">${tags}</div>
    </div>
  </div>
</div>`;
}

// ── Render ────────────────────────────────────────────────────────────────────
function renderDay(data) {
  currentTotal = data.total;
  const done = getProgress(currentDay);
  const n    = done.size;

  const titleParts = data.title.split(' ');
  const titleHtml  = titleParts.length >= 2
    ? titleParts[0] + '<br>' + titleParts.slice(1).join(' ')
    : data.title;

  const muscleTags = (data.muscle_tags || []).map(t => `<span class="tag">${t}</span>`).join('');

  let h = `<header data-day="${data.day_num}">
  <div class="label-day">Gym CAR — Nacho</div>
  <h1>${titleHtml}</h1>
  <div class="subtitle">${data.subtitle}</div>
  <div class="muscle-tags">${muscleTags}</div>
</header>
<div class="progress-wrap">
  <div class="progress-header">
    <span class="progress-label">Progreso</span>
    <span class="progress-count" id="countDisplay">${n} / ${data.total}</span>
  </div>
  <div class="progress-bar-bg">
    <div class="progress-bar-fill" id="progressBar" style="width:${n / data.total * 100}%"></div>
  </div>
</div>
<div class="content"><div style="height:18px"></div>`;

  let sectionShown = false;
  for (const ex of data.exercises) {
    const isDone = done.has(ex._id);
    if (ex.type === 'cardio') {
      h += buildCardioCard(ex, isDone);
      h += '<div class="section-title">Ejercicios · 4 × 12</div>';
      sectionShown = true;
    } else {
      if (!sectionShown) {
        h += '<div class="section-title">Ejercicios · 4 × 12</div>';
        sectionShown = true;
      }
      h += buildExCard(ex, isDone);
    }
  }

  h += `<div class="complete-banner${n === data.total ? ' show' : ''}" id="completeBanner">
  <div class="complete-emoji">🔥</div>
  <div class="complete-title">SESIÓN COMPLETADA</div>
  <div class="complete-sub">${data.title} terminado · Buen trabajo</div>
</div>
<div class="footer">GYM CAR · Nacho</div>
</div>`;

  document.getElementById('root').innerHTML = h;
  openDetail = null;
}

// ── Load day ──────────────────────────────────────────────────────────────────
async function loadDay(n) {
  if (currentDay === n) return;
  currentDay = n;
  openDetail = null;

  document.querySelectorAll('.tab').forEach((t, i) => t.classList.toggle('on', i === n - 1));
  document.getElementById('root').innerHTML =
    '<div class="loading"><div class="loading-dot"></div><div class="loading-dot"></div><div class="loading-dot"></div></div>';

  try {
    const data = await fetch('/api/day/' + n).then(r => {
      if (!r.ok) throw new Error(r.status);
      return r.json();
    });
    renderDay(data);
  } catch (err) {
    document.getElementById('root').innerHTML =
      '<div class="loading" style="color:#666;font-size:13px">Error cargando. Recarga la página.</div>';
  }
}

loadDay(1);
