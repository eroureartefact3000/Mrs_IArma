# Integration Guide — Mrs IArma

> For front-end & back-end developers integrating the prediction engine into a production app.

This document tells you exactly what the engine does, what it doesn't do, and where you plug your own code. Read it once before opening any file.

---

## TL;DR

```
┌────────────────┐         ┌───────────────────────────────┐
│  Your frontend │  HTTP   │     Mrs IArma engine          │
│  (Next.js,     ├────────▶│  pipeline/  (Python lib)      │
│  whatever)     │ JSON    │  api/       (FastAPI service) │
└────────────────┘         │  data/      (RAG index)       │
                           └───────────────────────────────┘
                                       ▲
                                       │
                                       ├──── ANTHROPIC_API_KEY
                                       ├──── VOYAGE_API_KEY
                                       └──── (no DB, no auth, no user state)
```

- **One endpoint matters**: `POST /api/evaluate`. Multipart upload + 5 form fields → JSON.
- **One Python function matters**: `pipeline.evaluate_board(image_path, user_metadata)`. Same contract.
- **Latency**: ~45 s per call. Budget for it. Show a loader.
- **Cost**: ~$1.90 in API calls (Anthropic + Voyage) per evaluation.
- **State**: zero. Engine doesn't persist anything. You bring the DB.

---

## 1. Repository structure

| Path | Purpose | Touch it? |
|---|---|---|
| `pipeline/` | The prediction engine (Python package, `mrs-iarma`). Public API in `pipeline/__init__.py`. | **No** — import only. |
| `api/` | Reference FastAPI service exposing the engine over HTTP. | **Yes** — replace with your own back-end stack if needed, or use as-is. |
| `frontend/` | Reference React + TS + Vite + Tailwind frontend (5-step wizard, "Mrs Airma · The Cannes Oracle" branding). Ready to deploy. | **Yes** — extend or replace as your real front-end. |
| `mini_frontend/` | Legacy vanilla-HTML smoke UI. Useful for sanity checks; not the production target. | Optional — kept for diagnostics. |
| `data/` | RAG indexes — one `{slug}_index.npy` + `{slug}_index_meta.jsonl` pair per enabled category (30 pairs in current build). Loaded lazily at runtime. | **No** — don't modify, but you can ship it inside your Docker image. |
| `scripts/` | Dev tools (rebuild index, calibration). Not needed in production. | Optional — use if you ever want to rebuild the index. |
| `tests/` | pytest smoke tests. | Read for examples. |
| `data_internal/` | Dev artefacts (calibration runs, drafts). **Gitignored**, not shipped. | Ignore. |

---

## 2. Public Python API

If your back-end is Python, the cleanest integration is to import the package directly.

### Install

```bash
# From the local clone
pip install -e .
# Or directly from GitHub
pip install "mrs-iarma @ git+https://github.com/artefact3000/mrs-iarma.git"
```

### Call

```python
from pathlib import Path
from pipeline import evaluate_board, UserMetadata, BoardEvaluation

result: BoardEvaluation = evaluate_board(
    image_path=Path("board.jpg"),
    user_metadata=UserMetadata(
        campaign_name="Phone Break",
        agency="VML Prague",
        client="KitKat",
        category="Outdoor",
        client_internationally_known=True,
    ),
    k_references=5,    # default: 5 winners + 2 non-winners auto-added
    n_passes=3,        # default: 3 parallel judge passes, averaged
)

# Primary user-facing output (what the front-end should display)
print(result.tier_prediction.tier_label)      # "GRAND PRIX LION"
print(result.tier_prediction.score_percent)   # 91
print(result.tier_prediction.confidence)      # "high"
print(result.tier_prediction.mystic_verdict)  # "The constellations align..."
print(result.tier_prediction.synthesis)       # 1-2 sentence diagnostic
print(result.tier_prediction.axes)            # 4 AxisScore
print(result.tier_prediction.presages)        # 3 Presage
```

### Public symbols (`pipeline/__init__.py`)

```python
# Entry point
evaluate_board(image_path, user_metadata, *, k_references=5, n_passes=3, exclude_ids=None) -> BoardEvaluation
DEFAULT_MEDAL_THRESHOLD: float                # 0.65, used internally

# Inputs
UserMetadata: BaseModel                       # campaign, agency, client, category, client_internationally_known

# Outputs
BoardEvaluation: BaseModel                    # full result envelope
TierPrediction: BaseModel                     # PRIMARY user-facing output
AxisScore: BaseModel                          # 1 axis (idea / strategy / execution / impact)
Presage: BaseModel                            # 1 omen (aesthetic / client / network)
MedalPrediction: BaseModel                    # internal binary prediction
BoardAnalysis: BaseModel                      # raw extraction
Reference: BaseModel                          # 1 RAG anchor

# Type aliases
PredictedTier   = Literal["Grand Prix", "Gold", "Silver", "Bronze", "No Medal"]
ConfidenceLabel = Literal["high", "medium", "low"]

# Errors
IndexNotBuilt(RuntimeError)                   # raised if data/{slug}_index.* missing for the requested category
```

---

## 3. Public HTTP API

If your back-end is not Python, talk to the FastAPI service.

### Endpoints

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/api/health` | none | Liveness probe. Returns version + `index_loaded` flag. |
| GET | `/api/categories` | none | List of Cannes Lions categories with `enabled` flag (for the front-end dropdown). |
| POST | `/api/evaluate` | optional `X-API-Key` | Full evaluation. ~45 s. |
| GET | `/docs` | none | OpenAPI / Swagger interactive docs. |

### Request — `POST /api/evaluate`

`Content-Type: multipart/form-data`

| Field | Type | Required | Notes |
|---|---|---|---|
| `image` | file | yes | board file: jpg / png / webp / avif / gif / **pdf** (multi-page case studies supported natively), ≤ 25 MB |
| `campaign_name` | string | yes | max 200 chars |
| `agency` | string | yes | used for the network malus detection |
| `client` | string | yes | display only |
| `category` | string | yes | one of the 30 enabled categories (see `/api/categories`). All Cannes Lions 2026 entry categories are wired. |
| `client_internationally_known` | bool | yes | `true` / `false` — used for the client malus |

### Response

```json
{
  "evaluation_id": "7176131d-a53c-4745-9e8c-29aca6565c03",
  "elapsed_seconds": 47.1,
  "tier_prediction": {
    "predicted_tier": "Grand Prix",
    "tier_label": "GRAND PRIX LION",
    "tier_probabilities": {
      "Grand Prix": 0.55,
      "Gold": 0.30,
      "Silver": 0.10,
      "Bronze": 0.03,
      "No Medal": 0.02
    },
    "confidence": "high",
    "score_percent": 91,
    "mystic_verdict": "The constellations align with this work.",
    "axes": [
      { "key": "idea", "label": "Creative Idea", "score": 95, "weight": 0.35 },
      { "key": "strategy", "label": "Strategy", "score": 93, "weight": 0.10 },
      { "key": "execution", "label": "Execution", "score": 90, "weight": 0.30 },
      { "key": "impact", "label": "Impact & Results", "score": 85, "weight": 0.25 }
    ],
    "presages": [
      { "type": "aesthetic", "kind": "favorable", "title": "Aesthetic board", "detail": "Legible composition, clean hierarchy.", "malus_pct": 0 },
      { "type": "client", "kind": "favorable", "title": "International client", "detail": "Brand recognised beyond borders.", "malus_pct": 0 },
      { "type": "network", "kind": "favorable", "title": "Holding favours this entry", "detail": "Omnicom network: favourable presage.", "malus_pct": 0 }
    ],
    "synthesis": "1-2 sentence post-mortem in oracle tone, English."
  },
  "_debug": {
    "medal_prediction": { "will_medal": true, "medal_probability": 0.98, "confidence": "high", "synthesis": "...", "threshold": 0.65 },
    "base_weighted_score": 91.8,
    "final_weighted_score": 91.8,
    "tier_probabilities": { "Grand Prix": 0.55, "Gold": 0.30, "Silver": 0.10, "Bronze": 0.03, "No Medal": 0.02 },
    "malus": { "aesthetic_applied": false, "client_applied": false, "network_applied": false, "detected_holding": "Omnicom", "multiplier": 1.0, "notes": ["Network: agency belongs to Omnicom → no malus"] },
    "references_count": 7
  }
}
```

**Front-end consumes `tier_prediction` only.** `_debug` is exposed for internal teams (calibration, support, A/B comparisons) — feel free to hide it.

### Example curl

```bash
curl -X POST http://localhost:8000/api/evaluate \
  -F "image=@board.jpg" \
  -F "campaign_name=Phone Break" \
  -F "agency=VML Prague" \
  -F "client=KitKat" \
  -F "category=Outdoor" \
  -F "client_internationally_known=true"
```

### Error responses

| Status | Reason |
|---|---|
| 400 | Bad category, bad file extension, missing fields |
| 401 | `X-API-Key` missing/wrong (only if `API_KEY` env var is set) |
| 413 | File too large (default cap 25 MB) |
| 422 | Pydantic validation failed |
| 429 | Rate limit exceeded |
| 500 | Engine error (pipeline failed). Check server logs. |
| 503 | Daily evaluation cap reached |

---

## 4. Environment variables

All configuration is via env vars. The `.env.example` lists every supported key.

| Variable | Required | Default | Notes |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | yes | — | Claude API key |
| `VOYAGE_API_KEY` | yes | — | Voyage AI key |
| `ENVIRONMENT` | no | `development` | `development` / `staging` / `production` |
| `LOG_LEVEL` | no | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `API_KEY` | no | `""` (empty = no auth) | Shared secret for `X-API-Key` header |
| `ALLOWED_ORIGINS` | no | `*` | Comma-separated CORS origins. Strict list in prod. |
| `RATE_LIMIT_PER_MINUTE` | no | `10` | 0 = disabled |
| `RATE_LIMIT_PER_HOUR` | no | `60` | 0 = disabled |
| `DAILY_EVALUATION_CAP` | no | `0` (unlimited) | Hard cap per UTC day. Set to e.g. 200 to protect your wallet on a public site. |
| `JUDGE_PASSES` | no | `3` | Number of parallel LLM-judge passes. Don't go below 2 — variance becomes too high. |
| `RAG_TOP_K` | no | `5` | Winner references retrieved. 2 non-winners are always added on top. |
| `MAX_UPLOAD_MB` | no | `25` | Hard cap on upload size |
| `SERVE_MINI_FRONTEND` | no | `true` | Set `false` for pure-API deployments |

---

## 5. Local development

### With Docker (recommended)

```bash
cp .env.example .env  # fill in ANTHROPIC_API_KEY and VOYAGE_API_KEY
docker compose up --build
```

Open <http://localhost:8000>. The mini frontend is at `/`, OpenAPI docs at `/docs`.

### Without Docker (Python directly)

```bash
cp .env.example .env  # fill in ANTHROPIC_API_KEY and VOYAGE_API_KEY
uv sync --all-extras  # installs api + dev + test extras
uv run uvicorn api.main:app --reload --port 8000
```

### Run tests

```bash
uv run pytest  # 20 smoke tests, ~1 s, no API calls
```

### Run a real evaluation from the CLI

```bash
uv run python scripts/evaluate_board.py \
  --image path/to/board.jpg \
  --campaign "Phone Break" \
  --agency "VML Prague" \
  --client "KitKat" \
  --client-international \
  --output result.json
```

---

## 6. Production deployment (GCP Cloud Run)

The Dockerfile is built for Cloud Run. The integrating data engineer should:

### 6.1 Build & push image

```bash
gcloud builds submit --tag europe-west1-docker.pkg.dev/<PROJECT>/<REPO>/mrs-iarma:latest
```

### 6.2 Deploy as Cloud Run service

```bash
gcloud run deploy mrs-iarma \
  --image europe-west1-docker.pkg.dev/<PROJECT>/<REPO>/mrs-iarma:latest \
  --region europe-west1 \
  --memory 1Gi --cpu 1 \
  --concurrency 4 \
  --timeout 120 \
  --min-instances 0 --max-instances 10 \
  --allow-unauthenticated \
  --set-secrets ANTHROPIC_API_KEY=anthropic-key:latest,VOYAGE_API_KEY=voyage-key:latest \
  --set-env-vars ENVIRONMENT=production,LOG_LEVEL=INFO,ALLOWED_ORIGINS=https://your-front.example.com,API_KEY-DEFER-TO-SECRET=true,DAILY_EVALUATION_CAP=500
```

Notes:
- **Memory**: 1 GiB is enough (the RAG index sits in ~50 MiB of RAM, peak during multi-pass LLM judging is ~500 MiB).
- **CPU**: 1 vCPU suffices — the engine is I/O-bound (LLM API calls).
- **Concurrency**: 4 simultaneous requests per instance. Each request takes ~45 s. Beyond 4, queueing kicks in. Adjust based on your traffic profile.
- **Timeout**: must be ≥ 60 s (LLM calls can spike on long boards).
- **Cold start**: ~5 s (loading the numpy index). Set `min-instances=1` to avoid it on production traffic.

### 6.3 Secret Manager for API keys

```bash
echo -n "sk-ant-..." | gcloud secrets create anthropic-key --data-file=-
echo -n "pa-..."     | gcloud secrets create voyage-key   --data-file=-
```

Then in Cloud Run, mount them via `--set-secrets` (see above). **Never commit keys to Git.**

### 6.4 Front-of-front protection

For a public website, put **Cloud Armor** in front for DDoS + bot defense. Use Cloud Armor's bot management or front the service with reCAPTCHA Enterprise / Cloudflare Turnstile. The in-process rate limit is a last line of defense, not the first.

### 6.5 Observability

The service logs structured JSON to stdout (Cloud Logging-compatible). Each request emits `request_method`, `request_path`, `status_code`, `elapsed_ms`, plus `evaluation_id` + `tier` for completed evaluations. Set up a log-based metric on `evaluation_completed` to monitor throughput.

For deeper tracing (per-step latency: extraction / RAG / judge / malus), the engine doesn't emit OpenTelemetry spans today — consider adding them if you need fine-grained perf monitoring. Hooks would go in `pipeline/evaluate.py`.

---

## 7. What the engine does NOT do (your responsibilities)

| Concern | Engine | Your back-end |
|---|---|---|
| User accounts / auth | ❌ | ✅ (SSO, OAuth, sessions) |
| Persistence (history of evaluations) | ❌ | ✅ (Postgres / Firestore) |
| GDPR / consent | ❌ | ✅ (especially if you keep board images) |
| Email / notifications | ❌ | ✅ |
| Background queue for long-running jobs | ❌ | ✅ (recommended: Cloud Tasks + workers) |
| Caching (same image uploaded twice) | ❌ | Optional — implement at the back-end layer with image hash → result mapping |
| Multi-language UI | The engine outputs English (oracle tone). Translate at the front-end layer if needed. | ✅ |
| Logging beyond stdout | stdout JSON only | ✅ (Cloud Logging / Datadog / etc.) |
| Image storage | Engine processes in-memory, deletes immediately | ✅ if you want to persist user uploads (GCS) |

---

## 8. Known limits & accuracy

- **Categories**: all 30 Cannes Lions 2026 entry categories are enabled with criteria, RAG indexes, and rationales. `/api/categories` returns the live list with `enabled` flags.
- **Accuracy** (formal calibration on Outdoor and PR; 28 other categories smoke-tested but not formally calibrated):
  - Outdoor (n=10 held-out): Binary 80%, within ±1 tier (argmax) 70%, exact tier (argmax) 30%.
  - PR (n=20 sweep): Binary 75%. See `data_internal/PR_CALIBRATION_NOTES.md`.
  - Print & Publishing (n=10): Binary 60%. See `data_internal/PRINT_CALIBRATION_NOTES.md`.
  - **System limit documented**: LLM-judge score compression in the 65-85 band makes exact-tier prediction inherently noisy. See `data_internal/SYSTEM_CALIBRATION_NOTES.md`. The UI must communicate predictions as **indicative**, and the `confidence` field on `TierPrediction` is your primary tool for that.
- **Latency**: 45 s average, 90 s worst case (large boards + retries).
- **Cost**: ~$1.90 per evaluation. Anthropic Opus is the dominant cost; Voyage embeddings are ~$0.0001.
- **Throughput**: roughly 1 evaluation per CPU per minute. Scale horizontally.

---

## 9. Rebuilding the RAG indexes

Each category has its own `data/{slug}_index.npy` + `data/{slug}_index_meta.jsonl`. The full set of 30 indexes is committed and shipped with the Docker image.

To rebuild a single category's index (e.g. after updating its extraction or rationale files):

```bash
uv run python scripts/build_index.py --category Outdoor
```

The full offline pipeline to regenerate a category end-to-end (source boards → extractions → rationales → index) uses Claude Code subagents (subscription mode, no per-call API spend) driven by the per-category briefs in `agent_briefs/categories/`:

```bash
# 1. Inventory the source folder into a batched manifest
uv run python scripts/inventory_boards.py --category "Print & Publishing" --batches 3

# 2. Dispatch subagents (see DOCUMENTATION.md § Subagent dispatch playbook)
#    The brief at agent_briefs/categories/PRINT.md is self-contained.

# 3. Generate winner rationales (subagents again, prompted by agent_briefs/why_won_brief.md)

# 4. Build the RAG index from the rationale file
uv run python scripts/build_index.py --category "Print & Publishing"
```

To add a brand-new category (beyond the 30 Cannes Lions 2026 categories already wired), the steps are:
1. Add a `{slug}_criteria.py` module under `pipeline/`.
2. Add a brief at `agent_briefs/categories/{SLUG}.md`.
3. Register the category in `pipeline/category_registry.py`.
4. Add its source-folder mapping in `scripts/inventory_boards.py`.
5. Run the 4 steps above to produce the index.

---

## 10. Contact

- **Engine maintainer**: Etienne Roure (etienne.roure@artefact.com)
- **Methodology details**: see `DOCUMENTATION.md` for the full development history (extraction schema decisions, calibration iterations, DA feedback patterns, etc.)
