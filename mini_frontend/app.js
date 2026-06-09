// Mini frontend de test pour Mrs IArma.
// Simple vanilla JS — pas de framework, le front prod sera développé par le front-end dev.

(() => {
  const API_BASE = window.location.origin;
  // If the API requires an X-API-Key header, set it here. For local dev with
  // an empty API_KEY env var, the backend disables auth. The production
  // front-end will inject this key via env-time config.
  const API_KEY = '';

  const views = {
    form: document.getElementById('view-form'),
    loading: document.getElementById('view-loading'),
    result: document.getElementById('view-result'),
    error: document.getElementById('view-error'),
  };

  function show(view) {
    Object.values(views).forEach(v => v.classList.remove('active'));
    views[view].classList.add('active');
  }

  // --- Load categories on init ---
  async function loadCategories() {
    const select = document.getElementById('category-select');
    const hint = document.getElementById('category-hint');
    try {
      const res = await fetch(`${API_BASE}/api/categories`);
      const data = await res.json();
      select.innerHTML = '';
      data.categories.forEach(cat => {
        const opt = document.createElement('option');
        opt.value = cat.key;
        opt.textContent = cat.label_fr + (cat.enabled ? '' : ' (bientôt disponible)');
        opt.disabled = !cat.enabled;
        if (cat.enabled) opt.selected = true;
        select.appendChild(opt);
      });
      hint.textContent = "Pour le MVP, seule la catégorie Outdoor est analysable.";
    } catch (err) {
      hint.textContent = "Impossible de charger les catégories. L'API est-elle démarrée ?";
    }
  }
  loadCategories();

  // --- File input feedback ---
  const fileInput = document.getElementById('image-input');
  const fileName = document.getElementById('file-name');
  fileInput.addEventListener('change', () => {
    if (fileInput.files && fileInput.files[0]) {
      const f = fileInput.files[0];
      const sizeMB = (f.size / (1024 * 1024)).toFixed(2);
      fileName.textContent = `${f.name} · ${sizeMB} Mo`;
    } else {
      fileName.textContent = "Aucun fichier sélectionné";
    }
  });

  // --- Submit ---
  document.getElementById('evaluation-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('submit-btn');
    btn.disabled = true;

    const form = e.target;
    const fd = new FormData();
    fd.append('campaign_name', form.campaign_name.value);
    fd.append('category', form.category.value);
    fd.append('client', form.client.value);
    fd.append('client_internationally_known', form.client_internationally_known.value);
    fd.append('agency', form.agency.value);
    fd.append('image', form.image.files[0]);

    show('loading');

    const headers = {};
    if (API_KEY) headers['X-API-Key'] = API_KEY;

    try {
      const res = await fetch(`${API_BASE}/api/evaluate`, {
        method: 'POST',
        body: fd,
        headers,
      });
      if (!res.ok) {
        const errBody = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(errBody.detail || `HTTP ${res.status}`);
      }
      const data = await res.json();
      renderResult(data.tier_prediction);
      show('result');
    } catch (err) {
      document.getElementById('error-detail').textContent = err.message;
      show('error');
    } finally {
      btn.disabled = false;
    }
  });

  document.getElementById('retry-btn').addEventListener('click', () => show('form'));
  document.getElementById('error-retry-btn').addEventListener('click', () => show('form'));

  // --- Render result ---
  function renderResult(tp) {
    const card = document.getElementById('result-card');
    const axesHtml = tp.axes.map(a => `
      <div class="axis-row">
        <span class="axis-label">${escape(a.label_fr)} <small>pondération ${Math.round(a.weight * 100)} %</small></span>
        <span class="axis-score">${a.score}/100</span>
        <div class="axis-bar"><span style="width: ${a.score}%"></span></div>
      </div>
    `).join('');

    const presagesHtml = tp.presages.map(p => `
      <div class="presage-row">
        <span class="presage-sign ${p.kind === 'favorable' ? 'fav' : 'con'}">${p.kind === 'favorable' ? '✓' : '✗'}</span>
        <span class="presage-body">
          <span class="presage-title">${escape(p.title)}</span>
          <span class="presage-detail">${escape(p.detail)}${p.malus_pct ? ` — ${p.malus_pct} %` : ''}</span>
        </span>
      </div>
    `).join('');

    card.innerHTML = `
      <div class="tier-hero">
        <div class="tier-circle">
          <span class="stamp">Mme Airma</span>
          <span class="tier-label">${escape(tp.tier_label_fr)}</span>
        </div>
        <div class="tier-score">${tp.score_percent}<sup>%</sup></div>
        <div class="verdict">« ${escape(tp.mystic_verdict)} »</div>
        <div class="confidence-badge">Confiance ${escape(tp.confidence)}</div>
      </div>

      <div class="panel">
        <div class="panel-title">Lecture détaillée des astres</div>
        ${axesHtml}
      </div>

      <div class="panel">
        <div class="panel-title">Présages détectés</div>
        ${presagesHtml}
      </div>

      <div class="synthesis-panel">${escape(tp.synthesis)}</div>
    `;
  }

  function escape(s) {
    if (s == null) return '';
    return String(s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
})();
