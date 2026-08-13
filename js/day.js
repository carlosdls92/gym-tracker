const TOTAL = parseInt(document.body.dataset.total, 10) || 10;
const done  = new Set();

function markBtn(btn, isDone) {
  btn.style.color       = isDone ? 'white'    : 'transparent';
  btn.style.background  = isDone ? '#4a9a4a'  : 'transparent';
  btn.style.borderColor = isDone ? '#4a9a4a'  : '#2a2a2a';
}

function updateProgress() {
  const n = done.size;
  document.getElementById('progressBar').style.width = (n / TOTAL * 100) + '%';
  document.getElementById('countDisplay').textContent = n + ' / ' + TOTAL;
  document.getElementById('completeBanner').classList.toggle('show', n === TOTAL);
}

function toggleCardio() {
  const card = document.getElementById('cardio');
  if (!card) return;
  const btn  = document.getElementById('cardioCheck');
  const isDone = card.classList.toggle('done');
  markBtn(btn, isDone);
  isDone ? done.add('c') : done.delete('c');
  updateProgress();
}

let openDetail = null;

function toggleCard(e, idx) {
  const btn = document.getElementById('check' + idx);
  if (e.target === btn || btn.contains(e.target)) {
    e.stopPropagation();
    const card   = document.getElementById('ex' + idx);
    const isDone = card.classList.toggle('done');
    markBtn(btn, isDone);
    if (isDone) {
      done.add(idx);
      card.classList.add('just-done');
      setTimeout(() => card.classList.remove('just-done'), 300);
    } else {
      done.delete(idx);
    }
    updateProgress();
    return;
  }
  const detail = document.getElementById('detail' + idx);
  if (openDetail && openDetail !== detail) openDetail.classList.remove('open');
  detail.classList.toggle('open');
  openDetail = detail.classList.contains('open') ? detail : null;
}
