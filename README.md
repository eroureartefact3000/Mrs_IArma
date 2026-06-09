# Mrs IArma · Cannes Lions Prediction Engine

> Predicts whether a Cannes Lions board entry will win, and which tier (Grand Prix / Gold / Silver / Bronze / No Medal). Built by [Artefact 3000](https://artefact.com).

## What this is

A prediction engine that takes a Cannes Lions board image + a few metadata fields, and returns a structured prediction with:

- Tier prediction (Grand Prix / Gold / Silver / Bronze / No Medal)
- Confidence label
- Per-axis scores (Idea / Strategy / Execution / Impact)
- 3 "présages" (favorable/contraire) reflecting the malus rules
- A 1-2 sentence post-mortem synthesis (French, mystic tone)

## Two integration paths

### As a Python library

```python
from pathlib import Path
from pipeline import evaluate_board, UserMetadata

result = evaluate_board(
    image_path=Path("board.jpg"),
    user_metadata=UserMetadata(
        campaign_name="Phone Break",
        agency="VML Prague",
        client="KitKat",
        category="Outdoor",
        client_internationally_known=True,
    ),
)

print(result.tier_prediction.tier_label_fr)  # "GRAND PRIX LION"
print(result.tier_prediction.score_percent)  # 89
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

## Repo structure

```
pipeline/         The prediction engine (Python lib)
api/              FastAPI reference service
mini_frontend/    Lightweight HTML test UI
scripts/          Dev scripts (rebuild index, calibration, etc.)
data/             Production assets (RAG index, committed)
tests/            Smoke tests
```

## Stack

- **Claude Opus 4.7** for VLM extraction & LLM-judge
- **Voyage AI** (`voyage-3-large`) for embeddings + RAG
- **FastAPI** for the HTTP service
- **Numpy** in-memory vector index (no DB needed)

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
```

Open <http://localhost:8000> for the mini frontend, or <http://localhost:8000/docs> for the OpenAPI spec.

```bash
uv run pytest                         # 20 smoke tests, ~1 s, no API calls
```

## Limits & maturity

- **MVP scope**: only the `Outdoor` Cannes Lions category is fully supported.
- **Accuracy**: ~80 % binary (medal vs no medal) on a 10-board held-out test set. See [DOCUMENTATION.md](DOCUMENTATION.md) for full calibration results.
- **Latency**: ~45 s per evaluation, ~$2 in API costs.
- **State**: stateless. No DB. Authentication and persistence are responsibilities of the integrating back-end.

## For integrators

- **[INTEGRATION.md](INTEGRATION.md)** — full integration guide (Python SDK, HTTP API, env vars, GCP deployment, what's NOT included).
- **[DOCUMENTATION.md](DOCUMENTATION.md)** — methodology, calibration history, decisions log.
