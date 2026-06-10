# Mrs IArma · The Cannes Oracle

> Cannes Lions tier prediction engine. Built by [Artefact 3000](https://artefact.com).

A prediction engine that reads a campaign board (image or PDF) and a few metadata fields, then returns a structured tier prediction with confidence, per-axis scores, and an oracle-tone narrative output.

## What it returns

For each board it predicts the Cannes Lions tier (Grand Prix / Gold / Silver / Bronze / No Medal) and ships:

- `tier_label` — e.g. `"GOLD LION"` / `"NO LION"`
- `score_percent` — headline figure 0-100
- `confidence` — high / medium / low (gap between top-1 and top-2 tier)
- `axes` — 4 axes (Creative Idea, Strategy, Execution, Impact & Results) with label + weight + score
- `presages` — 3 structured presages (favorable / unfavorable) reflecting the malus rules
- `mystic_verdict` — oracle-tone one-liner matching the predicted tier
- `synthesis` — 1-2 sentence post-mortem written by the judge

The whole output language is English. The runtime branding (frontend) is **"Mrs Airma · The Cannes Oracle"**.

## Coverage — 30 categories

All 30 Cannes Lions 2026 entry categories are wired with criteria, RAG index, and rationales. Full list:

| Family | Categories |
|---|---|
| **Classic** | Outdoor, Print & Publishing, Audio & Radio, Film |
| **Engagement** | PR, Direct, Media, Social & Influencer, Creative B2B, Creative Data |
| **Craft** | Design, Industry Craft, Digital Craft, Film Craft |
| **Experience** | Brand Experience & Activation, Creative Commerce, Creative Business Transformation, Innovation, Luxury |
| **Entertainment** | Entertainment, Entertainment Lions for Sport, Entertainment for Gaming, Entertainment for Music |
| **Health** | Health & Wellness, Pharma |
| **Good** | Sustainable Development Goals, Glass (The Lion for Change) |
| **Strategy** | Creative Strategy, Creative Effectiveness |
| **Titanium** | Titanium |

RAG reference base: 1466 boards extracted, 604 of them winners (with rationales).

## Two integration paths

### As a Python library

```python
from pathlib import Path
from pipeline import evaluate_board, UserMetadata

result = evaluate_board(
    image_path=Path("board.jpg"),  # or .pdf
    user_metadata=UserMetadata(
        campaign_name="Phone Break",
        agency="VML Prague",
        client="KitKat",
        category="Outdoor",
        client_internationally_known=True,
    ),
)

print(result.tier_prediction.tier_label)    # "GRAND PRIX LION"
print(result.tier_prediction.score_percent) # 89
```

### As an HTTP service

```bash
curl -X POST http://localhost:8000/api/evaluate \
  -F "image=@board.jpg" \
  -F "campaign_name=Phone Break" \
  -F "agency=VML Prague" \
  -F "client=KitKat" \
  -F "category=Outdoor" \
  -F "client_internationally_known=true"
```

## Documentation

- **[INTEGRATION.md](INTEGRATION.md)** — full integration guide for front-end and back-end developers
- **[DOCUMENTATION.md](DOCUMENTATION.md)** — technical history of the project (methodology, calibration, decisions)
- **[frontend/README.md](frontend/README.md)** — reference frontend (React + TS + Vite + Tailwind) handoff doc
- **[data_internal/SYSTEM_CALIBRATION_NOTES.md](data_internal/SYSTEM_CALIBRATION_NOTES.md)** — calibration limits documented

## Repo structure

```
pipeline/         The prediction engine (Python lib, 30 *_criteria.py modules)
api/              FastAPI reference service
frontend/         Reference frontend (React + TS + Vite + Tailwind)
mini_frontend/    Legacy vanilla-JS test UI (kept for reference)
scripts/          Dev scripts (inventory, build_index, evaluate, calibrate)
agent_briefs/     Markdown briefs used by Claude Code subagents for offline extraction
data/             Production assets (30 RAG indexes, committed)
design/           UI wireframes (not versioned in git, see .gitignore)
2024/             Source boards (not versioned in git, see .gitignore)
data_internal/    Extractions + rationales source (not versioned in git, regenerable)
tests/            Smoke tests
```

## Stack

- **Claude Opus 4.7** for VLM extraction & LLM-judge
- **Voyage AI** (`voyage-3-large`, 1024-dim) for embeddings + RAG
- **FastAPI** for the HTTP service
- **React + TS + Vite + Tailwind** for the reference frontend
- **Numpy** in-memory vector indexes (one per category, no DB)

## Quick start

```bash
git clone <repo>
cd Mrs_IArma
cp .env.example .env                  # fill in ANTHROPIC_API_KEY and VOYAGE_API_KEY

# Option A — Docker
docker compose up --build             # → http://localhost:8000

# Option B — Python directly
uv sync --all-extras                  # api + dev + test
uv run uvicorn api.main:app --reload  # → http://localhost:8000

# Frontend (separate terminal)
cd frontend
pnpm install && pnpm dev              # → http://localhost:5173
```

Open <http://localhost:5173> for the reference frontend, or <http://localhost:8000/docs> for the OpenAPI spec.

```bash
uv run pytest                         # smoke tests, ~1 s, no API calls
```

## Accepted file formats

`.jpg`, `.jpeg`, `.png`, `.webp`, `.avif`, `.gif`, **`.pdf`**. PDFs go natively to the Claude API (multi-page case studies are read in full, no conversion). Max upload size: 25 MB (configurable via `MAX_UPLOAD_MB`, hard ceiling 50 MB).

## Limits & maturity

- **Coverage**: 30/30 Cannes Lions 2026 categories enabled.
- **Calibration**: Outdoor and PR formally calibrated (80% and 75% binary accuracy on n=10 and n=20 sweeps). 28 other categories smoke-tested end-to-end but not formally calibrated. See `data_internal/SYSTEM_CALIBRATION_NOTES.md` for documented limits (score compression in the 65-85 band is a system-wide LLM-judge limitation, not a code bug).
- **Latency**: ~45 s per evaluation, ~$2 in API costs.
- **State**: stateless. No DB. Authentication and persistence are responsibilities of the integrating back-end.

## For integrators

- **[INTEGRATION.md](INTEGRATION.md)** — full integration guide (Python SDK, HTTP API, env vars, GCP deployment, what's NOT included).
- **[DOCUMENTATION.md](DOCUMENTATION.md)** — methodology, calibration history, decisions log.
- **[frontend/README.md](frontend/README.md)** — frontend handoff with React + TS + Vite + Tailwind setup and GCP deploy paths.
