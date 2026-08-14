let currentPlan  = null;
let currentDay   = 0;
let currentTotal = 0;
let openDetail   = null;
let plansCache   = null;

// ── Progress ──────────────────────────────────────────────────────────────────
function getProgress(plan, day) {
  try {
    const raw = localStorage.getItem(`gym-p-${plan}-${day}`);
    return raw ? new Set(JSON.parse(raw)) : new Set();
  } catch { return new Set(); }
}
function saveProgress(plan, day, done) {
  try { localStorage.setItem(`gym-p-${plan}-${day}`, JSON.stringify([...done])); } catch {}
}

function updateProgress() {
  const n      = getProgress(currentPlan, currentDay).size;
  const bar    = document.getElementById('progressBar');
  const count  = document.getElementById('countDisplay');
  const banner = document.getElementById('completeBanner');
  if (bar)    bar.style.width = (n / currentTotal * 100) + '%';
  if (count)  count.textContent = n + ' / ' + currentTotal;
  if (banner) banner.classList.toggle('show', currentTotal > 0 && n === currentTotal);
}

// ── Toggle ────────────────────────────────────────────────────────────────────
function toggleItem(e, id) {
  const btn = document.getElementById('chk-' + id);
  if (!btn) return;

  if (e.target === btn || btn.contains(e.target)) {
    e.stopPropagation();
    const card   = document.getElementById('card-' + id);
    const isDone = card.classList.toggle('done');
    btn.style.cssText = isDone ? 'color:white;background:#4a9a4a;border-color:#4a9a4a' : '';
    const done = getProgress(currentPlan, currentDay);
    isDone ? done.add(id) : done.delete(id);
    saveProgress(currentPlan, currentDay, done);
    updateProgress();
    if (isDone) {
      card.classList.add('just-done');
      setTimeout(() => card.classList.remove('just-done'), 300);
    }
    return;
  }

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

function buildDots(sets) {
  return Array.from({ length: sets || 4 }, () => '<div class="set-dot"></div>').join('');
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
  const dc   = isDone ? ' done' : '';
  const g0   = ex.gifs[0] || {};
  const g1   = ex.gifs[1] || {};
  const tags = (ex.tags || []).map(t => `<span class="detail-tag">${t}</span>`).join('');
  const sets = ex.sets || 4;
  const reps = ex.reps || '12';
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
      <div class="sets-row">${buildDots(sets)}</div>
      <div class="reps-label">${sets}×${reps}</div>
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

// ── Render day ────────────────────────────────────────────────────────────────
function renderDay(data) {
  currentTotal = data.total;
  const done = getProgress(currentPlan, currentDay);
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
      h += '<div class="section-title">Ejercicios</div>';
      sectionShown = true;
    } else {
      if (!sectionShown) {
        h += '<div class="section-title">Ejercicios</div>';
        sectionShown = true;
      }
      h += buildExCard(ex, isDone);
    }
  }

  h += `<div class="complete-banner${n === data.total && data.total > 0 ? ' show' : ''}" id="completeBanner">
  <div class="complete-emoji">🔥</div>
  <div class="complete-title">SESIÓN COMPLETADA</div>
  <div class="complete-sub">${data.title} terminado · Buen trabajo</div>
</div>
<div class="footer">GYM CAR · Nacho</div>
</div>`;

  document.getElementById('root').innerHTML = h;
  openDetail = null;
}

// ── Tabs ──────────────────────────────────────────────────────────────────────
function renderTabs(planSlug, days) {
  const tabs = document.getElementById('tabs-bar');
  tabs.innerHTML =
    `<button class="tab tab-back" onclick="showPlanSelector()">←</button>` +
    days.map(d =>
      `<button class="tab${d.day_num === currentDay ? ' on' : ''}" data-day="${d.day_num}" onclick="loadDay('${planSlug}',${d.day_num})">${d.day_label}</button>`
    ).join('') +
    `<a class="tab-dl" href="/api/plan/${planSlug}/offline" download="gym-${planSlug}.html" title="Descargar offline">↓</a>`;
}

// ── Load day ──────────────────────────────────────────────────────────────────
async function loadDay(plan, dayNum) {
  if (currentPlan === plan && currentDay === dayNum) return;
  currentPlan = plan;
  currentDay  = dayNum;
  openDetail  = null;

  document.querySelectorAll('.tab[data-day]').forEach(t =>
    t.classList.toggle('on', parseInt(t.dataset.day) === dayNum)
  );

  document.getElementById('root').innerHTML =
    '<div class="loading"><div class="loading-dot"></div><div class="loading-dot"></div><div class="loading-dot"></div></div>';

  try {
    const data = await fetch(`/api/plan/${plan}/day/${dayNum}`).then(r => {
      if (!r.ok) throw new Error(r.status);
      return r.json();
    });
    renderDay(data);
    localStorage.setItem('gym-last-plan', plan);
    localStorage.setItem('gym-last-day',  String(dayNum));
  } catch {
    document.getElementById('root').innerHTML =
      '<div class="loading" style="color:#666;font-size:13px">Error cargando. Recarga la página.</div>';
  }
}

// ── Plan selector ─────────────────────────────────────────────────────────────
async function showPlanSelector() {
  currentPlan = null;
  currentDay  = 0;
  openDetail  = null;

  document.getElementById('tabs-bar').innerHTML = '<div class="tabs-title">GYM CAR</div>';
  document.getElementById('root').innerHTML =
    '<div class="loading"><div class="loading-dot"></div><div class="loading-dot"></div><div class="loading-dot"></div></div>';

  try {
    plansCache = await fetch('/api/plans').then(r => r.json());

    let h = `<div class="plan-selector">
  <div class="plan-selector-header">
    <div class="label-day">Gym CAR — Nacho</div>
    <h1 class="plan-selector-title">ELIGE<br>PLAN</h1>
  </div>`;

    for (const plan of plansCache) {
      const labels = plan.days.map(d => d.day_label).join(' · ');
      h += `<div class="plan-card" onclick="selectPlan('${plan._id}')">
  <div class="plan-card-inner">
    <div class="plan-card-name">${plan.name}</div>
    <div class="plan-card-meta">${plan.days.length} días · ${labels}</div>
  </div>
  <div class="plan-card-actions">
    <a class="plan-dl-btn" href="/api/plan/${plan._id}/offline" download="gym-${plan._id}.html" onclick="event.stopPropagation()" title="Descargar para uso offline">↓</a>
    <div class="plan-card-arrow">→</div>
  </div>
</div>`;
    }

    h += '</div>';
    document.getElementById('root').innerHTML = h;
  } catch {
    document.getElementById('root').innerHTML =
      '<div class="loading" style="color:#666;font-size:13px">Error cargando planes.</div>';
  }
}

// ── Select plan ───────────────────────────────────────────────────────────────
async function selectPlan(slug) {
  if (!plansCache) {
    plansCache = await fetch('/api/plans').then(r => r.json());
  }
  const plan = plansCache.find(p => p._id === slug);
  if (!plan) return;
  renderTabs(slug, plan.days);
  loadDay(slug, plan.days[0].day_num);
}

// ── Init ──────────────────────────────────────────────────────────────────────
(async () => {
  const lastPlan = localStorage.getItem('gym-last-plan');
  const lastDay  = parseInt(localStorage.getItem('gym-last-day') || '0');

  if (lastPlan && lastDay) {
    try {
      plansCache = await fetch('/api/plans').then(r => r.json());
      const plan = plansCache.find(p => p._id === lastPlan);
      if (plan) {
        renderTabs(lastPlan, plan.days);
        await loadDay(lastPlan, lastDay);
        return;
      }
    } catch { /* fall through to selector */ }
  }

  showPlanSelector();
})();
