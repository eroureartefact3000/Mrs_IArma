# Handoff — Mrs IArma · The Cannes Oracle

> Engine author: Etienne Roure (etienne.roure@artefact.com).
> Status as of 2026-06-10: engine complete, dockerised, ready to deploy.

---

## What this is

A Cannes Lions tier prediction engine. Upload a campaign board (image or PDF),
get a structured prediction: tier (Grand Prix / Gold / Silver / Bronze / No Medal),
0-100 score, 4 axis scores, 3 presages, an oracle-tone synthesis.

- 30 / 30 Cannes Lions 2026 entry categories enabled
- Stack: Python 3.11 + FastAPI (backend) · React 18 + Vite + Tailwind (frontend)
- Runs as **one container** that serves `/api/*` and `/` from the same origin

---

## What you're inheriting

```
.
├── pipeline/      → prediction engine (Python lib, 30 *_criteria.py modules)
├── api/           → FastAPI service (the /api/* endpoints)
├── frontend/      → React reference UI ("Mrs Airma · The Cannes Oracle")
├── data/          → 30 RAG indexes (numpy + JSONL), committed, ~50 MiB total
├── Dockerfile     → multi-stage: frontend build → python venv → runtime
├── docker-compose.yml
├── .env.example   → exhaustive list of every env var the API reads
└── tests/         → 25 smoke tests, ~1 s, no API calls
```

---

## Boot the stack in 90 seconds

```bash
# 1. Secrets
cp .env.example .env
# Fill ANTHROPIC_API_KEY and VOYAGE_API_KEY (the only two required values)

# 2. Build + run
docker compose up --build
# → http://localhost:8000      reference frontend
# → http://localhost:8000/docs OpenAPI (Swagger)
# → http://localhost:8000/api/health   → {status:"ok", index_loaded:true}
```

Smoke test (manual, the dockerised stack should return a Grand Prix on this):

```bash
cp "2024/OUTDOOR/GRAND PRIX/Adoptable - Pedigree (Colenso BBDO, Auckland).webp" /tmp/board.webp
curl -X POST http://localhost:8000/api/evaluate \
  -F image=@/tmp/board.webp \
  -F campaign_name=Adoptable \
  -F "agency=Colenso BBDO" \
  -F client=Pedigree \
  -F category=Outdoor \
  -F client_internationally_known=true
# ~45-50 s, ~$2 in real API spend, returns Grand Prix 90/100 high confidence
```

---

## Where to go next

| If you want to… | Read this |
|---|---|
| Understand the contract (HTTP + Python SDK) | [`INTEGRATION.md`](INTEGRATION.md) — exhaustive, written for you |
| Deploy to GCP Cloud Run | `INTEGRATION.md` §6 — gcloud commands + Secret Manager + Cloud Armor notes |
| Understand the methodology & calibration scope | [`DOCUMENTATION.md`](DOCUMENTATION.md) — engineering history (French; engine output is English) |
| Frame the calibration limits to stakeholders | `data_internal/SYSTEM_CALIBRATION_NOTES.md` (gitignored — ask Etienne) |
| Add a 31st category later | `INTEGRATION.md` §9 — 5-step recipe |

---

## What's deliberately NOT included

The engine is stateless. None of the following are its responsibility — they
belong to whatever back-end wraps it in production:

- User accounts / SSO / auth (the engine accepts an optional `X-API-Key` shared secret)
- Persistence of evaluations (no DB)
- Image storage (uploads are processed in memory and discarded)
- GDPR / consent flow
- Email / notifications
- Background queue for long jobs (each call is ~45 s synchronous — wrap in your own queue if needed)
- Caching by image hash
- Multi-language UI

---

## Known limits

- **Latency**: ~45 s per evaluation, 90 s worst case
- **Cost**: ~$2 in API calls per evaluation (Anthropic dominant; Voyage ~$0.0001)
- **Throughput**: ~1 evaluation per vCPU per minute → scale horizontally
- **Accuracy**: Outdoor 80% binary, PR 75% binary on held-out sets. The 28 other
  categories are smoke-tested end-to-end but not formally calibrated. The judge
  compresses weighted scores in the 65-85 band — this is an LLM-judge limit,
  not a code bug. Communicate predictions as **indicative**; the `confidence`
  field on `TierPrediction` is the primary tool for that.

---

## Pre-deploy checklist

Before exposing the service publicly:

- [ ] `ANTHROPIC_API_KEY` and `VOYAGE_API_KEY` in Secret Manager (never in the image)
- [ ] `API_KEY` set to a strong random secret + matching `VITE_API_KEY` injected into the frontend build
- [ ] `ALLOWED_ORIGINS` set to the production frontend domain (not `*`)
- [ ] `DAILY_EVALUATION_CAP` set (e.g. 200) — protects your wallet against bot traffic
- [ ] Cloud Armor or equivalent in front for DDoS / bot filtering — the in-process rate limit is a last line of defense, not the first
- [ ] Cloud Run timeout ≥ 60 s (LLM calls can spike); concurrency ≤ 4 per instance

---

## Who to call

- **Engine maintainer**: Etienne Roure — etienne.roure@artefact.com
- **Repo**: see `git remote -v` (Artefact GitHub)
