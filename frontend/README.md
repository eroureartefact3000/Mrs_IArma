# Mrs Airma · The Cannes Oracle — Reference Frontend

A React + TypeScript + Vite + Tailwind reference implementation of the UI for
the Mrs IArma prediction engine. **This is a reference, not a finished
product**: a frontend dev + UX/UI designer are expected to pick it up and
polish it for public release.

What's in here:
- ✅ Full state machine wired to the backend (form → loading → result → error)
- ✅ Typed API client matching `pipeline.schema` Pydantic models
- ✅ The "sun rays" signature motif as an SVG component (`SunRays.tsx`)
- ✅ All 4 mockup states translated to English (form, loading, result, error)
- ✅ Multi-step Typeform-style form wizard (5 questions, Enter to advance)
- ✅ Tailwind config with the Mrs Airma palette (cream/ink/gold-bronze-silver)

What's intentionally **not** done (handoff to the UX dev):
- ❌ Pixel-perfect match with the mockups (composition is right, micro-details aren't)
- ❌ Real share/export functionality (Share button copies URL only)
- ❌ Mobile-specific layout tuning
- ❌ Animations between form steps
- ❌ History of past evaluations
- ❌ A11y review (basic ARIA only)
- ❌ Tests
- ❌ Storybook for the components
- ❌ i18n (currently English-only, French copy in the mockups is gone)

## Quick start (local dev)

```bash
cd frontend
pnpm install        # or npm install / yarn install
pnpm dev            # runs Vite dev server on :5173
```

In a second terminal, start the backend:
```bash
cd ..
uv run uvicorn api.main:app --reload --port 8000
```

The Vite dev server proxies `/api/*` to `localhost:8000`, so the frontend
talks to the backend without CORS noise.

Open http://localhost:5173 in your browser.

## Build for production

```bash
pnpm build           # outputs static files to frontend/dist/
pnpm preview         # serves dist/ locally to sanity check
```

## Project structure

```
frontend/
├── package.json               # React 18 + Vite 5 + Tailwind 3
├── vite.config.ts             # dev proxy for /api
├── tsconfig.json
├── tailwind.config.js         # Mrs Airma palette + custom fonts
├── index.html                 # loads Cormorant Garamond + Inter from Google Fonts
└── src/
    ├── main.tsx               # React root
    ├── App.tsx                # State machine (form/loading/result/error)
    ├── api.ts                 # Typed API client (POST /api/evaluate, GET /api/categories)
    ├── types.ts               # TS types matching pipeline.schema
    ├── styles/index.css       # Tailwind base + .editorial, .label-caps, .cta-* utility classes
    └── components/
        ├── Header.tsx
        ├── SunRays.tsx        # Signature radiating-capsules motif (SVG)
        ├── FormWizard.tsx     # Multi-step form
        ├── Loading.tsx        # Oracle loading state
        ├── ResultPage.tsx     # Tier result with axes + presages
        ├── AxesTable.tsx
        ├── PresagesList.tsx
        └── ErrorPage.tsx
```

## API contract

The frontend calls two endpoints, both on the same origin:

### `GET /api/categories`
Returns the list of supported Cannes Lions categories. The wizard's category
dropdown shows only `enabled: true` entries.
```json
{
  "categories": [
    { "key": "Outdoor", "label": "Outdoor", "family": "Classic", "enabled": true },
    { "key": "PR",      "label": "PR",      "family": "Engagement", "enabled": true }
    // ...
  ]
}
```

### `POST /api/evaluate`
multipart/form-data with:
- `campaign_name` (string, 1-200 chars)
- `agency` (string, 1-200 chars)
- `client` (string, 1-200 chars)
- `category` (string, must match one enabled key)
- `client_internationally_known` (`"true"` | `"false"`)
- `image` (file: jpg/png/webp/avif/gif, ≤25MB)

Returns:
```ts
interface EvaluateResponse {
  evaluation_id: string;
  elapsed_seconds: number;
  tier_prediction: TierPrediction;  // see src/types.ts
  // _debug field is present but the UI doesn't surface it
}
```

Errors return `{ "detail": "..." }` with a non-2xx status. The frontend
displays the `detail` on the error page.

### Auth (production)

The backend reads `API_KEY` from env. If set, the frontend must send
`X-API-Key: <key>` on every request. Configure via:
```bash
# frontend/.env.local (gitignored)
VITE_API_KEY=your-key-here
```
The Vite build inlines this at compile time.

## GCP deployment — two viable paths

### Path A — Single Cloud Run service (simplest, recommended for v1)

Bundle the frontend + backend together. FastAPI serves the static files.

1. Build the frontend:
   ```bash
   cd frontend && pnpm build
   ```
2. Mount `frontend/dist/` in FastAPI (`api/main.py`):
   ```python
   from fastapi.staticfiles import StaticFiles
   app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")
   # Make sure this is mounted LAST, after all /api routes.
   ```
3. Update the `Dockerfile` to copy `frontend/dist/` and the frontend build step.
4. `gcloud run deploy mrs-iarma --source=. --region=europe-west1`

**Pros**: one service, one deploy, no CORS, no separate hosting.
**Cons**: frontend is rebuilt on every backend deploy.

### Path B — Firebase Hosting (frontend) + Cloud Run (backend)

Split the two concerns for independent deploys.

1. Frontend → Firebase Hosting:
   ```bash
   cd frontend
   pnpm build
   firebase deploy --only hosting
   ```
   With a `firebase.json` rewrite that routes `/api/*` to the Cloud Run service:
   ```json
   {
     "hosting": {
       "public": "frontend/dist",
       "rewrites": [
         { "source": "/api/**", "run": { "serviceId": "mrs-iarma-api", "region": "europe-west1" } },
         { "source": "**", "destination": "/index.html" }
       ]
     }
   }
   ```
2. Backend → Cloud Run (existing `Dockerfile`):
   ```bash
   gcloud run deploy mrs-iarma-api --source=. --region=europe-west1
   ```

**Pros**: independent deploy cycles, Firebase CDN, free hosting tier.
**Cons**: two services to maintain, slightly more setup.

## Handoff checklist for the next dev

- [ ] Run `pnpm install && pnpm dev` and confirm it boots
- [ ] Verify all 4 views render (use a real backend, or stub `api.ts`)
- [ ] Match pixel-level details to the latest Figma (the wireframes here are early)
- [ ] Implement the Share action (PDF? shareable URL with server-side persistence?)
- [ ] Add step-to-step animations on the form (CSS or Framer Motion)
- [ ] Mobile audit — test < 640px breakpoints
- [ ] A11y pass — keyboard navigation in the wizard, screen reader labels
- [ ] Decide auth flow — single API key inlined at build vs. user-account auth
- [ ] Storybook + Vitest if the team standardises on those
- [ ] Pick GCP path A or B with the team and write the deploy script

## Design source

Wireframes live in `../design/` at the repo root. They are early-stage and in
French — the visual language (cream paper, India-ink black, serif italic, sun
rays, presage cards) is correct, but copy and exact spacing should be redone
with the UX/UI designer before public release.
