const form = document.getElementById('mood-form');
const input = document.getElementById('mood-input');
const btn = document.getElementById('submit-btn');
const loading = document.getElementById('loading');
const error = document.getElementById('error');
const results = document.getElementById('results');

const ICONS = { movie: '🎬', show: '📺', book: '📖', comic: '💥' };
const LABELS = { movie: 'Movie', show: 'TV Show', book: 'Book', comic: 'Comic' };

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const mood = input.value.trim();
  if (!mood) return;

  setLoading(true);
  hideError();
  results.classList.add('hidden');

  try {
    const res = await fetch('/recommend', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mood }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Something went wrong' }));
      throw new Error(err.detail || 'Something went wrong');
    }
    const data = await res.json();
    renderCards(data);
    results.classList.remove('hidden');
  } catch (err) {
    showError(err.message);
  } finally {
    setLoading(false);
  }
});

function renderCards(data) {
  for (const type of ['movie', 'show', 'book', 'comic']) {
    const card = document.getElementById(`card-${type}`);
    const rec = data[type];
    if (!rec) { card.innerHTML = ''; continue; }

    const thumbHtml = rec.thumb
      ? `<img class="card-thumb" src="${rec.thumb}" alt="${esc(rec.title)}" loading="lazy" onerror="this.replaceWith(makePlaceholder('${ICONS[type]}'))">`
      : `<div class="card-thumb-placeholder">${ICONS[type]}</div>`;

    const linkHtml = rec.deep_link
      ? `<a class="card-link" href="${rec.deep_link}" target="_blank">Open in ${LABELS[type] === 'Book' ? 'Calibre' : LABELS[type] === 'Comic' ? 'Komga' : 'Plex'}</a>`
      : '';

    card.innerHTML = `
      <span class="card-label">${LABELS[type]}</span>
      ${thumbHtml}
      <div class="card-body">
        <div class="card-title">${esc(rec.title)}</div>
        <div class="card-pitch">${esc(rec.pitch)}</div>
        ${linkHtml}
      </div>`;
  }
}

function makePlaceholder(icon) {
  const div = document.createElement('div');
  div.className = 'card-thumb-placeholder';
  div.textContent = icon;
  return div;
}

function esc(str) {
  return String(str || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function setLoading(on) {
  btn.disabled = on;
  loading.classList.toggle('hidden', !on);
}

function showError(msg) {
  error.textContent = msg;
  error.classList.remove('hidden');
}

function hideError() {
  error.classList.add('hidden');
}
