"""Generate a single self-contained HTML to review the 65 PR extractions.

Reads data/pr_with_rationale.jsonl and writes review.html at the project root.
The HTML embeds all records as JSON inside a <script> tag and references board
images by relative path, so you can open review.html directly with file://.

Usage:
    uv run python build_review_ui.py
    open review.html
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IN_PATH = ROOT / "data_internal" / "pr_with_rationale.jsonl"
OUT_PATH = ROOT / "data_internal" / "review.html"

TIER_ORDER = {"Grand Prix": 0, "Gold": 1, "Silver": 2, "Bronze": 3}


def main() -> None:
    records = []
    for line in IN_PATH.open():
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not r.get("error") and r.get("why_it_won"):
            records.append(r)

    records.sort(
        key=lambda r: (
            TIER_ORDER.get(r["tier"], 99),
            -r["why_it_won"]["weighted_score"],
        )
    )

    payload = json.dumps(records, ensure_ascii=False)
    # Defensive: avoid breaking the <script> tag if any value contains "</script>"
    payload = payload.replace("</script>", "<\\/script>")

    html = _HTML.replace("__DATA__", payload)
    OUT_PATH.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT_PATH} ({len(records)} boards, {len(html) // 1024} KB)")


_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Mrs IArma · PR Review</title>
<style>
  :root {
    --fg: #111;
    --fg-soft: #555;
    --fg-faint: #888;
    --bg: #fafaf8;
    --card: #ffffff;
    --border: #e4e4e0;
    --hl: #1a1a1a;
    --accent: #b8860b;
    --gold: #d4af37;
    --silver: #b8b8b8;
    --bronze: #b87333;
    --ok: #2d6e3e;
    --warn: #b58105;
    --bad: #a8302a;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { background: var(--bg); color: var(--fg); }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Helvetica, Arial, sans-serif;
    font-size: 14px;
    line-height: 1.55;
    -webkit-font-smoothing: antialiased;
  }
  code, pre { font-family: "SF Mono", "JetBrains Mono", Menlo, monospace; }

  /* Top bar */
  .topbar {
    position: sticky; top: 0; z-index: 20;
    background: rgba(255,255,255,0.95);
    backdrop-filter: blur(8px);
    border-bottom: 1px solid var(--border);
    padding: 0.9rem 1.4rem;
    display: flex; flex-wrap: wrap; gap: 1.2rem; align-items: center;
  }
  .topbar h1 {
    font-size: 0.95rem; font-weight: 600;
    letter-spacing: 0.02em;
  }
  .stats { font-size: 0.8rem; color: var(--fg-faint); }
  .filter-group { display: flex; gap: 0.3rem; align-items: center; font-size: 0.78rem; color: var(--fg-faint); }
  .filter-group label { font-weight: 500; margin-right: 0.3rem; }
  .filter-btn {
    padding: 0.25rem 0.65rem;
    border: 1px solid var(--border);
    background: white;
    cursor: pointer;
    border-radius: 999px;
    font-size: 0.78rem; font-family: inherit; color: var(--fg-soft);
    transition: all 0.12s ease;
  }
  .filter-btn:hover { background: #f0f0ec; color: var(--fg); }
  .filter-btn.active { background: var(--hl); color: white; border-color: var(--hl); }
  .search {
    margin-left: auto;
    padding: 0.32rem 0.7rem;
    border: 1px solid var(--border);
    border-radius: 999px;
    font-size: 0.8rem; font-family: inherit;
    background: white; min-width: 200px;
  }

  /* Container */
  .container { max-width: 1400px; margin: 0 auto; padding: 1.6rem; }

  /* Card */
  .card {
    display: grid;
    grid-template-columns: minmax(340px, 480px) 1fr;
    gap: 2rem;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.4rem;
    margin-bottom: 1.5rem;
    transition: border-color 0.15s;
  }
  .card[data-flagged="true"] { border-color: var(--warn); border-width: 2px; }
  .card.collapsed .content-side { display: none; }

  /* Image side */
  .image-side { position: sticky; top: 5rem; align-self: start; }
  .image-side img {
    width: 100%;
    border-radius: 4px;
    cursor: zoom-in;
    background: #f0f0f0;
    display: block;
  }
  .image-meta {
    margin-top: 0.45rem;
    font-size: 0.7rem; color: var(--fg-faint);
    font-family: "SF Mono", monospace;
    word-break: break-all;
  }

  /* Tier + meta badges */
  .badges { display: flex; flex-wrap: wrap; gap: 0.35rem; margin-bottom: 0.55rem; }
  .badge {
    display: inline-flex; align-items: center;
    padding: 0.18rem 0.55rem;
    border-radius: 999px;
    font-size: 0.68rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.04em;
  }
  .badge-tier-grand-prix { background: #111; color: white; }
  .badge-tier-gold       { background: var(--gold); color: #1a1a1a; }
  .badge-tier-silver     { background: var(--silver); color: #1a1a1a; }
  .badge-tier-bronze     { background: var(--bronze); color: white; }
  .badge-meta { background: #f0f0ec; color: var(--fg-soft); }

  /* Content side */
  .one-liner {
    font-size: 1.4rem; font-weight: 600;
    line-height: 1.25; margin: 0.4rem 0 0.8rem;
    color: var(--hl);
  }
  .campaign-meta {
    font-size: 0.85rem; color: var(--fg-soft);
    margin-bottom: 1.2rem;
  }
  .campaign-meta strong { color: var(--fg); font-weight: 600; }

  /* Scores grid */
  .scores {
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 0.4rem;
    margin-bottom: 0.7rem;
  }
  .axis {
    padding: 0.6rem 0.7rem;
    background: #f7f7f3;
    border-radius: 6px;
    border: 1px solid #ececea;
  }
  .axis-label {
    font-size: 0.65rem;
    text-transform: uppercase; letter-spacing: 0.06em;
    color: var(--fg-faint); font-weight: 600;
  }
  .axis-weight {
    font-size: 0.62rem; color: var(--fg-faint); font-weight: 400;
  }
  .axis-score {
    font-size: 1.5rem; font-weight: 700;
    color: var(--hl);
    margin-top: 0.1rem;
    font-feature-settings: "tnum";
  }

  /* Total */
  .total {
    display: flex; align-items: center; gap: 0.6rem;
    padding: 0.7rem 0.9rem;
    background: var(--hl);
    color: white;
    border-radius: 6px;
    margin: 0.5rem 0 1rem;
  }
  .total-label { font-size: 0.75rem; opacity: 0.7; text-transform: uppercase; letter-spacing: 0.06em; }
  .total-score { font-size: 1.6rem; font-weight: 700; font-feature-settings: "tnum"; }
  .consistency {
    margin-left: auto;
    font-size: 0.65rem; font-weight: 600;
    padding: 0.2rem 0.55rem;
    border-radius: 999px;
    text-transform: uppercase; letter-spacing: 0.05em;
  }
  .consistency-expected { background: rgba(45,110,62,0.25); color: #b0e0bc; }
  .consistency-above    { background: rgba(181,129,5,0.3); color: #ffd97a; }
  .consistency-below    { background: rgba(168,48,42,0.3); color: #ffb1ab; }

  /* Verdict */
  .verdict {
    font-style: italic;
    padding: 0.9rem 1.1rem;
    background: #faf8f0;
    border-left: 3px solid var(--accent);
    border-radius: 0 6px 6px 0;
    margin-bottom: 1.2rem;
    color: #2a2a26;
    line-height: 1.55;
  }

  /* Rationales */
  .rationales h3 {
    font-size: 0.72rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.08em;
    color: var(--fg-faint); margin-bottom: 0.5rem;
  }
  .rationale { margin-bottom: 0.7rem; }
  .rationale-head { font-size: 0.72rem; font-weight: 600; color: var(--fg-soft); margin-bottom: 0.2rem; }
  .rationale-text { color: #333; font-size: 0.88rem; line-height: 1.5; }

  /* Tags */
  .section-label {
    font-size: 0.7rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.06em;
    color: var(--fg-faint);
    margin: 1.2rem 0 0.4rem;
  }
  .tags { display: flex; flex-wrap: wrap; gap: 0.3rem; }
  .tag {
    padding: 0.18rem 0.55rem;
    background: #edf0f7;
    color: #2d4a7a;
    border-radius: 999px;
    font-size: 0.7rem;
    font-family: "SF Mono", monospace;
  }

  /* Details/JSON */
  details {
    margin-top: 1rem;
    border-top: 1px solid #efefec;
    padding-top: 0.6rem;
  }
  summary {
    cursor: pointer;
    font-weight: 600;
    color: var(--fg-soft);
    font-size: 0.78rem;
    user-select: none;
  }
  summary:hover { color: var(--hl); }
  details pre {
    background: #f8f8f4;
    border: 1px solid #ecece8;
    padding: 0.9rem;
    border-radius: 6px;
    font-size: 0.72rem;
    white-space: pre-wrap;
    overflow-x: auto;
    max-height: 420px;
    overflow-y: auto;
    margin-top: 0.6rem;
    line-height: 1.45;
  }

  /* Notes row */
  .notes-row {
    display: flex; gap: 0.5rem; margin-top: 1.2rem;
    padding-top: 1rem;
    border-top: 1px solid #efefec;
    align-items: center;
  }
  .mark-btn {
    padding: 0.4rem 0.8rem;
    border: 1px solid var(--border);
    background: white;
    cursor: pointer;
    border-radius: 6px;
    font-size: 0.78rem; font-family: inherit;
    color: var(--fg-soft);
    transition: all 0.12s;
  }
  .mark-btn:hover { background: #f7f7f3; }
  .mark-btn.on { background: var(--warn); color: white; border-color: var(--warn); }
  .notes-input {
    flex: 1;
    padding: 0.42rem 0.7rem;
    border: 1px solid var(--border);
    border-radius: 6px;
    font-size: 0.82rem; font-family: inherit;
    background: white;
  }
  .notes-input:focus { outline: none; border-color: var(--accent); }

  /* Image modal */
  .modal {
    display: none;
    position: fixed; inset: 0;
    background: rgba(0,0,0,0.95);
    z-index: 100;
    align-items: center; justify-content: center;
    padding: 2rem;
    cursor: zoom-out;
  }
  .modal.show { display: flex; }
  .modal img { max-width: 100%; max-height: 100%; box-shadow: 0 12px 60px rgba(0,0,0,0.6); }

  /* Responsive */
  @media (max-width: 980px) {
    .card { grid-template-columns: 1fr; }
    .image-side { position: static; }
    .scores { grid-template-columns: repeat(2, 1fr); }
  }
</style>
</head>
<body>

<div class="topbar">
  <h1>Mrs IArma · PR Review</h1>
  <span class="stats" id="stats"></span>
  <div class="filter-group">
    <label>Tier:</label>
    <div id="filter-tier"></div>
  </div>
  <div class="filter-group">
    <label>Consistency:</label>
    <div id="filter-consistency"></div>
  </div>
  <div class="filter-group">
    <label>Flagged:</label>
    <button class="filter-btn" id="filter-flagged" onclick="toggleFlaggedFilter()">All</button>
  </div>
  <input type="text" class="search" placeholder="Search campaign, brand…" id="search" oninput="setSearch(this.value)">
</div>

<div class="container" id="cards"></div>

<div class="modal" id="modal" onclick="this.classList.remove('show')">
  <img id="modal-img" src="" alt="">
</div>

<script>
const DATA = __DATA__;

const state = {
  tier: 'all',
  consistency: 'all',
  flagged: false,
  search: '',
};

const TIER_FILTERS = ['all', 'Grand Prix', 'Gold', 'Silver', 'Bronze'];
const CONS_FILTERS = ['all', 'expected', 'above', 'below'];

const escapeHtml = (s) => String(s == null ? '' : s)
  .replace(/&/g, '&amp;').replace(/</g, '&lt;')
  .replace(/>/g, '&gt;').replace(/"/g, '&quot;');

const tierClass = (t) => 'badge-tier-' + t.toLowerCase().replace(/\s+/g, '-');

function loadNotes() {
  try { return JSON.parse(localStorage.getItem('mrs_iarma_notes') || '{}'); }
  catch { return {}; }
}
function saveNotes(notes) { localStorage.setItem('mrs_iarma_notes', JSON.stringify(notes)); }

function buildFilters() {
  const tierRoot = document.getElementById('filter-tier');
  tierRoot.innerHTML = TIER_FILTERS.map(t =>
    `<button class="filter-btn ${state.tier === t ? 'active' : ''}" data-filter="tier" data-value="${escapeHtml(t)}">${t === 'all' ? 'All' : escapeHtml(t)}</button>`
  ).join('');

  const consRoot = document.getElementById('filter-consistency');
  consRoot.innerHTML = CONS_FILTERS.map(c =>
    `<button class="filter-btn ${state.consistency === c ? 'active' : ''}" data-filter="consistency" data-value="${escapeHtml(c)}">${c === 'all' ? 'All' : escapeHtml(c)}</button>`
  ).join('');

  const flaggedBtn = document.getElementById('filter-flagged');
  flaggedBtn.classList.toggle('active', state.flagged);
  flaggedBtn.textContent = state.flagged ? 'Flagged only' : 'All';
}

// Event delegation for filter buttons (more robust than inline onclick).
document.addEventListener('click', (e) => {
  const filterBtn = e.target.closest('.filter-btn[data-filter]');
  if (filterBtn) {
    setFilter(filterBtn.dataset.filter, filterBtn.dataset.value);
    return;
  }
  const flagBtn = e.target.closest('.mark-btn[data-card-id]');
  if (flagBtn) {
    toggleFlag(flagBtn.dataset.cardId);
  }
});

function setFilter(key, value) {
  state[key] = value;
  buildFilters();
  render();
}

function toggleFlaggedFilter() {
  state.flagged = !state.flagged;
  buildFilters();
  render();
}

function setSearch(v) {
  state.search = v;
  render();
}

function render() {
  const notes = loadNotes();
  const filtered = DATA.filter(r => {
    if (state.tier !== 'all' && r.tier !== state.tier) return false;
    if (state.consistency !== 'all' && r.why_it_won.tier_consistency !== state.consistency) return false;
    if (state.flagged && !(notes[r.id] || {}).flagged) return false;
    if (state.search) {
      const s = state.search.toLowerCase();
      const hay = [r.id, r.extracted.campaign, r.extracted.brand, r.inferred.one_liner, r.why_it_won.verdict]
        .filter(Boolean).join(' ').toLowerCase();
      if (!hay.includes(s)) return false;
    }
    return true;
  });

  document.getElementById('stats').textContent = `${filtered.length} / ${DATA.length}`;

  document.getElementById('cards').innerHTML = filtered.map(r => renderCard(r, notes[r.id] || {})).join('');
}

function renderCard(r, note) {
  const w = r.why_it_won;
  const flagged = !!note.flagged;
  const noteText = escapeHtml(note.note || '');
  const mechs = (r.inferred.creative_mechanisms || []).map(m =>
    `<span class="tag">${escapeHtml(m)}</span>`
  ).join('');

  const axisCard = (label, weight, score) =>
    `<div class="axis">
       <div class="axis-label">${label} <span class="axis-weight">${weight}%</span></div>
       <div class="axis-score">${score}</div>
     </div>`;

  const rationaleLine = (key, label) =>
    `<div class="rationale">
       <div class="rationale-head">${label} — ${w[key].score}/100</div>
       <div class="rationale-text">${escapeHtml(w[key].rationale)}</div>
     </div>`;

  const jsonPreview = JSON.stringify({
    extracted: r.extracted,
    inferred: r.inferred,
    visual: r.visual,
  }, null, 2);

  return `
  <div class="card" data-id="${escapeHtml(r.id)}" data-flagged="${flagged}">
    <div class="image-side">
      <img src="${encodeURI(r.file_path)}" alt="${escapeHtml(r.id)}" loading="lazy" onclick="zoom(this.src)">
      <div class="image-meta">${escapeHtml(r.file_path)}</div>
    </div>

    <div class="content-side">
      <div class="badges">
        <span class="badge ${tierClass(r.tier)}">${escapeHtml(r.tier)}</span>
        <span class="badge badge-meta">${escapeHtml(r.category)}</span>
        <span class="badge badge-meta">${escapeHtml(r.impact_strength)} impact</span>
        <span class="badge badge-meta">${(r.inferred.one_liner || '').split(' ').length}w one-liner</span>
      </div>

      <div class="one-liner">${escapeHtml(r.inferred.one_liner)}</div>
      <div class="campaign-meta">
        <strong>${escapeHtml(r.extracted.campaign || '?')}</strong>
        ${r.extracted.brand ? '· ' + escapeHtml(r.extracted.brand) : ''}
      </div>

      <div class="scores">
        ${axisCard('Idea', 20, w.idea.score)}
        ${axisCard('Strategy', 30, w.strategy.score)}
        ${axisCard('Execution', 20, w.execution.score)}
        ${axisCard('Impact', 30, w.impact.score)}
      </div>

      <div class="total">
        <span class="total-label">Weighted total</span>
        <span class="total-score">${w.weighted_score}</span>
        <span class="consistency consistency-${w.tier_consistency}">${w.tier_consistency}</span>
      </div>

      <div class="verdict">${escapeHtml(w.verdict)}</div>

      <div class="rationales">
        <h3>Per-axis rationale</h3>
        ${rationaleLine('idea', 'Idea (20%)')}
        ${rationaleLine('strategy', 'Strategy (30%)')}
        ${rationaleLine('execution', 'Execution (20%)')}
        ${rationaleLine('impact', 'Impact & Results (30%)')}
      </div>

      <div class="section-label">Creative mechanisms</div>
      <div class="tags">${mechs}</div>

      <details>
        <summary>Show raw extraction (extracted / inferred / visual)</summary>
        <pre>${escapeHtml(jsonPreview)}</pre>
      </details>

      <div class="notes-row">
        <button class="mark-btn ${flagged ? 'on' : ''}" data-card-id="${escapeHtml(r.id)}">${flagged ? '⚑ Flagged' : '⚐ Flag for review'}</button>
        <input class="notes-input" placeholder="Your note (saved locally)…" value="${noteText}" data-id="${escapeHtml(r.id)}" oninput="setNote(this.dataset.id, this.value)">
      </div>
    </div>
  </div>`;
}

function zoom(src) {
  document.getElementById('modal-img').src = src;
  document.getElementById('modal').classList.add('show');
}

function toggleFlag(id) {
  const notes = loadNotes();
  notes[id] = notes[id] || {};
  notes[id].flagged = !notes[id].flagged;
  saveNotes(notes);
  render();
}

function setNote(id, value) {
  const notes = loadNotes();
  notes[id] = notes[id] || {};
  notes[id].note = value;
  saveNotes(notes);
}

window.exportNotes = function () {
  const notes = loadNotes();
  const blob = new Blob([JSON.stringify(notes, null, 2)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'review_notes.json';
  a.click();
};

// Keyboard: Escape closes modal
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') document.getElementById('modal').classList.remove('show');
});

buildFilters();
render();
console.log("Tip: call exportNotes() in this console to download your flags + notes as JSON.");
</script>

</body>
</html>
"""


if __name__ == "__main__":
    main()
