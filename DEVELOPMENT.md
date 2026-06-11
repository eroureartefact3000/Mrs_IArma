# Development playbook

> How to pick this project back up after a break and make changes safely.
> Aimed at the original author (Etienne) and any future contributor.

---

## 1. Fast environment check (90 seconds)

Run these and confirm they all return cleanly. Stop and fix the first one that doesn't.

```bash
cd ~/Documents/Mrs_IArma

# 1. Python toolchain
uv --version                # any 0.4.x is fine
uv sync --all-extras        # installs api + dev + test in .venv/

# 2. Node toolchain (for frontend work)
node --version              # need v22+
corepack enable && pnpm --version

# 3. Docker (for end-to-end checks)
docker version --format 'client {{.Client.Version}} | server {{.Server.Version}}'

# 4. Secrets
test -f .env && grep -E "^(ANTHROPIC|VOYAGE)_API_KEY=." .env && echo "secrets OK"

# 5. Tests pass locally
uv run pytest -q            # expect: 25 passed
```

If any of these fail, read the matching section in `README.md` or
`INTEGRATION.md` before continuing.

---

## 2. Spin up the stack locally

### Option A: native (fastest iteration loop)

Two terminals:

```bash
# Terminal 1: backend
uv run uvicorn api.main:app --reload --port 8000

# Terminal 2: frontend
cd frontend && pnpm dev      # → http://localhost:5173
```

Vite proxies `/api/*` to `localhost:8000`. Code changes reload automatically.

### Option B: docker (matches production)

```bash
docker compose up --build    # → http://localhost:8000 (UI + API on one origin)
```

### Smoke test the live stack

```bash
# Copy a known board to a path without parens (curl chokes on parens)
cp "2024/OUTDOOR/GRAND PRIX/Adoptable - Pedigree (Colenso BBDO, Auckland).webp" /tmp/board.webp

curl -X POST http://localhost:8000/api/evaluate \
  -F image=@/tmp/board.webp \
  -F campaign_name=Adoptable \
  -F "agency=Colenso BBDO" \
  -F client=Pedigree \
  -F category=Outdoor \
  -F client_internationally_known=true
```

Expected: HTTP 200, `predicted_tier: "Grand Prix"`, score in the high 80s
or low 90s, ~45-55 seconds, ~$2 in API spend.

---

## 3. Where things live (map of the repo)

```
.
├── pipeline/                  PRODUCTION ENGINE (Python lib)
│   ├── evaluate.py            entry point: evaluate_board()
│   ├── extractor.py           VLM extraction (Claude Opus)
│   ├── rationale.py           why-it-won generator (offline)
│   ├── search.py              RAG retrieval (numpy + Voyage)
│   ├── judge.py               multi-pass tier judgment
│   ├── presentation.py        TierPrediction packaging
│   ├── category_registry.py   30 categories registered here
│   └── {slug}_criteria.py     30 criteria modules (one per category)
│
├── api/                       FASTAPI SERVICE
│   ├── main.py                app factory + static frontend mount
│   ├── routes.py              /api/* endpoints
│   ├── config.py              env var schema (pydantic-settings)
│   └── middleware.py          CORS, auth, rate limiting
│
├── frontend/                  REACT REFERENCE UI
│   ├── src/App.tsx            top-level wizard + result switch
│   ├── src/components/        FormWizard, CategoryDropdown, etc.
│   └── src/api.ts             typed client for /api/*
│
├── data/                      30 RAG INDEXES (.npy + .jsonl pairs)
├── data_internal/             gitignored: extractions, rationales, calibration notes
├── agent_briefs/categories/   MECE briefs used by subagents for offline extraction
├── scripts/                   inventory_boards.py, build_index.py, evaluate_board.py
└── tests/                     25 smoke tests (no API calls)
```

---

## 4. The five reference docs and when to read each

| Doc | When to read |
|---|---|
| `README.md` | Setup, repo structure, one-screen overview |
| `PROJECT_OVERVIEW.md` | Goal, value, journey, stack. Marketing-friendly |
| `HANDOFF.md` | Deploy-team brief (one page) |
| `INTEGRATION.md` | Full API contract, env vars, deploy commands, "what's NOT included" |
| `DOCUMENTATION.md` | Engineering history in French: extraction schema decisions, calibration iterations, DA feedback patterns |

---

## 5. Common modification recipes

### 5.1 Add a new Cannes Lions category

Five steps. Typical effort: 2-4 hours for a thin category, a full day
for a rich one (more boards = longer subagent extraction time).

1. **Create the criteria module.** `pipeline/{slug}_criteria.py`. Copy
   `pipeline/outdoor_criteria.py` and adjust axis weights + signals.
2. **Write the MECE brief.** `agent_briefs/categories/{SLUG}.md`. Copy
   any existing brief and adapt: native-to-category check, common
   patterns, RIGOUR reminders. The brief is what Claude Code subagents
   will read when extracting.
3. **Add to inventory mapping.** Append entries in `scripts/inventory_boards.py`
   under `CATEGORY_DIRS` and `CATEGORY_SLUG`.
4. **Run the offline pipeline.**
   ```bash
   uv run python scripts/inventory_boards.py --category "<Key>" --batches 3
   # Then dispatch subagents per the inventory output (see DOCUMENTATION.md §5)
   # Finally:
   uv run python scripts/build_index.py --category "<Key>"
   ```
5. **Register in the engine.** Add a block in `pipeline/category_registry.py`
   under the wave-2 specs list. Run `uv run pytest -q` to confirm
   `test_registry_has_thirty_enabled_categories` becomes
   `test_registry_has_thirty_one_enabled_categories` (you'll need to
   update the assertion count).

### 5.2 Retune calibration on an existing category

1. Curate a held-out test set: 10-20 boards with known tiers, NOT in
   `data/{slug}_index.npy`.
2. Run `uv run python scripts/calibrate.py --category "<Key>" --test-set <path>`
   (adapt from `scripts/calibrate_outdoor.py` if needed).
3. Inspect outputs in `data_internal/{slug}_calibration_<date>.jsonl`.
4. If the LLM-judge plateaus, options are: (a) prompt tightening (try
   adjusting the RIGOUR patterns in `pipeline/judge.py`), (b) raise
   `JUDGE_PASSES` (default 3), (c) consider the supervised ML layer
   documented in `DOCUMENTATION.md` §Phase 3.5.

### 5.3 Change the frontend copy or design system

```bash
cd frontend && pnpm dev      # → http://localhost:5173
```

Edit files in `frontend/src/`. The design system tokens live in
`frontend/src/styles/`. Sticky family headers in the dropdown live in
`frontend/src/components/CategoryDropdown.tsx`. Type checks run on
`pnpm lint` and during `pnpm build`.

**Important constraint**: no em dashes (—) in any user-visible text.
Saved as a feedback memory; honour it.

### 5.4 Bump dependencies

```bash
uv lock --upgrade            # Python deps → review pyproject.toml + uv.lock
cd frontend && pnpm update --latest  # Frontend deps
```

Then re-run `uv run pytest -q` and `pnpm build` to confirm nothing broke.
For Docker, rebuild from scratch with `docker compose build --no-cache`
and re-run the smoke test in §2.

### 5.5 Fix a prediction bug

The pipeline has five stages (extraction → retrieval → judge → malus →
presentation). To isolate which one is misbehaving, run the engine with
verbose logging:

```python
from pipeline import evaluate_board, UserMetadata
from pathlib import Path

result = evaluate_board(
    image_path=Path("/tmp/board.webp"),
    user_metadata=UserMetadata(...),
    verbose=True,     # prints intermediate state per stage
)
```

The verbose output shows the raw extraction, the retrieved references,
each pass of the judge, and the malus calculation. The bug is almost
always either in the extraction (board misread) or the judge prompt
(scoring band off).

---

## 6. Resuming a Claude Code session on this project

### 6.1 What Claude Code already knows

Auto-loaded into every session in this directory:

- The repo layout (via filesystem tools)
- `MEMORY.md` and the linked memory files at
  `~/.claude/projects/-Users-etienne-roure-Documents-Mrs-IArma/memory/`
  These include: user role, no-em-dash rule, DA mental model, score
  discrimination rule, the deferred ML layer roadmap, project state
  snapshots.

### 6.2 Prompt to bring back full context at session start

Paste this verbatim into Claude Code on a fresh session:

```
I'm resuming work on Mrs IArma (Cannes Lions tier prediction engine).
Read README.md, PROJECT_OVERVIEW.md, HANDOFF.md, and the memory index
at MEMORY.md. Then summarize back to me in 5 bullet points: (1) what
the engine does, (2) what state the codebase is in (categories
covered, calibration status), (3) what you remember about my working
style, (4) what is currently uncommitted or unpushed, (5) what I
should NOT do in this codebase. Wait for my next instruction before
writing any code.
```

This forces Claude Code to ground itself in the durable artefacts and
exposes any stale memory before you start coding.

### 6.3 Useful prompts for common tasks

| Task | Prompt to paste |
|---|---|
| Add a category | "Add support for the Cannes Lions `<Category Name>` category. Follow the 5-step recipe in DEVELOPMENT.md §5.1. Stop after step 1 (criteria module) and wait for review before continuing." |
| Re-run calibration | "Calibrate the engine on `<Category>` against a fresh 20-board held-out set. Use the methodology documented in DOCUMENTATION.md §5 (Phase 3.5). Report binary accuracy, ±1 tier accuracy, and Brier score." |
| Tune a prompt | "Read pipeline/judge.py. The current synthesis is too `<characteristic>`. Propose a prompt diff that addresses this without breaking the 5 RIGOUR patterns. Show me the diff first; do not apply it." |
| Frontend tweak | "Open frontend/src/components/`<file>`.tsx and `<describe change>`. Run pnpm build to confirm types pass. Do not push." |
| Verify everything still works | "Run pytest, build the Docker image, run one evaluation against /tmp/board.webp through the dockerised stack with category=Outdoor. Report tier, score, latency. Then tear the container down." |
| Cut a release | "Look at git log since the last tag. Draft a changelog entry grouped by feat/fix/docs/build. Show me the draft; do not tag yet." |

### 6.4 Before letting Claude commit or push

The author has set up dedicated GitHub auth via the `github-artefact`
SSH host alias. Confirm:

```bash
git remote -v
# expected: origin → git@github-artefact:eroureartefact3000/Mrs_IArma.git
```

If the remote is the personal GitHub account (no `github-artefact`),
stop and reconfigure SSH before pushing. The Artefact key alias is
documented in `~/.ssh/config`.

---

## 7. Gotchas this codebase will hit you with

These bit us during development; they are documented so you don't
spend an hour rediscovering each one.

### Docker / pnpm

- `node:22-alpine` is required, not 20. pnpm 11 (pulled by corepack)
  needs Node 22+.
- pnpm 11 enforces two policies that fail CI silently:
  `--config.minimumReleaseAge=0` skips the 24-hour supply-chain
  quarantine on lockfile entries, `--config.dangerouslyAllowAllBuilds=true`
  pre-approves postinstall scripts (esbuild needs one). Env vars and
  `.npmrc` keys are ignored. Only `--config` CLI flags work.
- `pnpm build` runs an implicit deps-status check that re-triggers
  the supply-chain policy. Bypass it by calling `./node_modules/.bin/tsc -b`
  and `./node_modules/.bin/vite build` directly.
- The host's `frontend/node_modules` will clobber the freshly-installed
  one inside the image if `.dockerignore` does not exclude it.

### Python builder

- `uv venv` does NOT include pip. Don't try `pip install -e .` inside
  the venv. Use `PYTHONPATH=/app` instead (already set in the Dockerfile).
- hatchling needs `README.md` AND the `pipeline/` source to build the
  wheel during `uv pip install .[api]`. Both must be COPYed in the
  builder stage.

### Curl edge cases

- File paths with parentheses break `curl -F image=@<path>`. Copy the
  test board to `/tmp/<simple-name>.webp` first.

### Calibration plateaus

- The LLM-judge compresses scores in the 65-85 band. Don't try to
  fix this with prompt engineering alone. The supervised ML layer
  in `DOCUMENTATION.md` §Phase 3.5 is the recovery path.

### Branding

- "Mrs Airma" (runtime brand) vs "Mrs IArma" (engine / repo name) is
  intentional. Don't unify them.

---

## 8. Pre-commit checklist

Before every commit (especially before a push):

```bash
uv run pytest -q                       # 25 tests, < 1 second
grep -rn "—" pipeline/ api/ frontend/src/ *.md   # em dash sweep
git status --short                     # nothing surprising
git diff --cached --stat               # only the files you meant
```

For commits touching the Docker stage or env config:

```bash
docker compose build                   # exercises the multi-stage
docker compose up -d
curl -sf http://localhost:8000/api/health   # smoke
docker compose down
```

---

## 9. Contacts

- **Engine maintainer**: Etienne Roure (etienne.roure@artefact.com)
- **Memory index**: `~/.claude/projects/-Users-etienne-roure-Documents-Mrs-IArma/memory/MEMORY.md`
- **Issue tracker**: not configured. Add one if you start receiving real bug reports.
