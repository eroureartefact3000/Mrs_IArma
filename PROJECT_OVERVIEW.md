# Mrs IArma · The Cannes Oracle

> Project overview for non-engineering stakeholders.
> Built by Artefact 3000. Lead: Etienne Roure.

---

## What we built

An AI prediction engine that reads a Cannes Lions campaign board (the
one-page visual that ad agencies submit to the jury) and predicts the
tier it would win: Grand Prix, Gold, Silver, Bronze, or No Medal.

The user uploads a board (image or PDF), fills in five fields (campaign
name, agency, client, category, international scope), and within about
45 seconds receives a structured verdict:

- A predicted tier with confidence (high / medium / low)
- A 0-to-100 score
- Four sub-scores along the canonical Cannes judging axes
  (Creative Idea, Strategy, Execution, Impact & Results)
- Three "presages" (favorable or unfavorable signals based on aesthetic,
  client recognition, and agency network)
- A one or two sentence diagnostic synthesis in an oracle-style tone

The output is published as a website (the runtime brand is
**"Mrs Airma · The Cannes Oracle"**) and as an HTTP API that other
Artefact properties can integrate.

---

## Why we built it

Two audiences, two value propositions.

### For Artefact 3000

A flagship marketing artefact in the year of Cannes Lions: a publicly
accessible AI tool that demonstrates Artefact's command of generative AI,
applied to a creative-industry use case the entire ad world watches.

### For creative agencies and creatives worldwide

Free, instant, structured feedback on the "Cannes-ability" of a piece of
work. The output is not just a score, it is a per-axis breakdown anchored
to real reference winners. A creative team can see *which* axis their work
is weakest on, and *which* past winner their work most resembles.

---

## The 30 categories we cover

All thirty 2026 Cannes Lions entry categories, grouped by family:

| Family | Categories |
|---|---|
| **Classic** | Outdoor · Print & Publishing · Audio & Radio · Film |
| **Engagement** | PR · Direct · Media · Social & Influencer · Creative B2B · Creative Data |
| **Craft** | Design · Industry Craft · Digital Craft · Film Craft |
| **Experience** | Brand Experience & Activation · Creative Commerce · Creative Business Transformation · Innovation · Luxury |
| **Entertainment** | Entertainment · Entertainment Lions for Sport · Entertainment for Gaming · Entertainment for Music |
| **Health** | Health & Wellness · Pharma |
| **Good** | Sustainable Development Goals · Glass (The Lion for Change) |
| **Strategy** | Creative Strategy · Creative Effectiveness |
| **Titanium** | Titanium |

Each category has its own judging criteria, its own weighting of the four
axes (a Craft category leans heavily on Execution, a Strategy category on
Impact, an Outdoor on Idea), and its own library of past winners to
compare against.

---

## What made this hard

Cannes is not a leaderboard with a numerical winner. It is a jury of
creative directors discussing taste, originality, cultural impact, and
craft. Replacing that conversation with software meant solving four
problems that machine learning typically does not solve well.

### 1. The dataset is tiny and qualitative

A single Cannes category may have only 50 to 120 past winners in a year.
That is not enough to train a classifier from scratch, and the "labels"
(Grand Prix, Gold, etc.) are themselves the *output* of a subjective
expert deliberation, not ground truth.

### 2. The judging criteria are not numbers

A jury talks about whether an idea is "category-redefining" or whether an
execution is "Craft-tier." Encoding these intuitions required a custom
schema, a per-category brief, and a feedback loop with a Senior Art
Director from Artefact who corrected the model's reasoning over multiple
review cycles.

### 3. Different categories judge differently

Outdoor weights Idea at 35% and Execution at 30%. Industry Craft weights
Execution at 55%. Creative Effectiveness weights Impact at 55%. We could
not ship a one-size-fits-all model. We built thirty different criteria
modules, each calibrated to the relevant 2026 Cannes Lions entry kit.

### 4. Naming what makes a "Cannes-grade" idea

Through iteration with the Art Director we extracted five recurring
rigour patterns that distinguish jury-grade work from "good agency work."
These now run on every evaluation. Examples:

- Unanchored percentages (a "+300% lift" with no baseline) get flagged
- Press claims with no auditable source are downgraded
- Superlatives without specifics are penalised
- Cultural nuances are named explicitly (a Quebec joke is not pan-Canadian)
- The "native to category" check (is this really an Outdoor idea, or just
  a great Film with an Outdoor adaptation?)

---

## How it works

In plain language: the engine simulates a jury deliberation. It "reads"
the board, retrieves the most conceptually similar past winners from a
reference library, and asks a large language model to score the work
*against those specific references* on four axes. It does this three
times in parallel with different seeds, then averages, which makes the
output stable and removes the worst LLM hallucinations.

### The five-step pipeline

1. **Extraction.** Claude Opus 4.7 reads the board image (or PDF) and
   produces a structured JSON capturing the campaign idea, strategy,
   execution, and reported metrics. PDFs of multi-page case studies
   are read natively, no conversion needed.

2. **Retrieval.** The board is converted to an embedding via Voyage AI
   (a 1024-dimension semantic vector). The engine retrieves the 5 most
   similar past winners plus 2 deliberate non-winners (to give the judge
   a real range, not just success cases).

3. **Multi-pass judgment.** Claude Opus 4.7 scores the new board on four
   axes, three times in parallel, with the retrieved references in
   context. The three passes are averaged.

4. **Presage system.** Three rule-based modifiers ("malus") adjust the
   score for aesthetic quality, client international recognition, and
   agency-network heritage. These reflect observable Cannes biases.

5. **Presentation.** The final tier, score, axes, presages and synthesis
   are packaged into the oracle-style output the user sees.

---

## The tech stack

| Layer | Technology | Why |
|---|---|---|
| Reasoning & extraction | **Claude Opus 4.7** (Anthropic) | State-of-the-art VLM; supports native PDF reading |
| Semantic search | **Voyage AI** (`voyage-3-large`, 1024-dim) | Best-in-class general-purpose embeddings |
| Vector index | **NumPy** in-memory | 30 indexes × ~50 boards each fit in RAM. No DB needed |
| Backend | **Python 3.11 + FastAPI** | Async, well-typed, OpenAPI out-of-the-box |
| Frontend | **React 18 + TypeScript + Vite + Tailwind** | Editorial design system ("Mrs Airma · The Cannes Oracle") |
| Container | **Multi-stage Docker** (Node 22 → Python 3.11) | One artefact serves API and frontend together |
| Cloud target | **Google Cloud Run** | Auto-scaling, pay-per-request, fits Artefact's GCP stack |
| Offline dataset prep | **Claude Code subagents** | Subscription-mode orchestration, zero per-call API cost during dataset construction |

The engine is **stateless** by design. No database. No user accounts.
This is intentional: it makes Mrs IArma cheap to host, easy to integrate
inside larger Artefact properties, and trivial to scale horizontally.

---

## Development journey

A six-phase build, May to June 2026.

| Phase | What we did | Outcome |
|---|---|---|
| **1. Methodology** | Designed the LLM-as-Judge + RAG approach. Validated the v3 extraction schema with the Senior Art Director on PR 2025 (65 boards) | Proof of concept, two corrections from the Art Director on the prompt structure |
| **2. Outdoor v1** | Pivoted to Outdoor 2024 (better-organized dataset). Built the first per-category index | First end-to-end evaluations, ~70% binary accuracy |
| **3. Rigour patterns** | Art Director identified five recurring rigour misses. Encoded them into the prompt | Loser scores fell 6 points, calibration tightened |
| **4. Binary calibration** | Refactored the judge to a tool-use API. Added 2 non-winners to the RAG to break the "everything is a medal" bias | **80% binary accuracy on Outdoor**, validated on a 10-board held-out test |
| **5. Multi-category extension** | Built per-category briefs (29 more), criteria modules, and RAG indexes. Used Claude Code subagents to extract 1466 boards in parallel | **30 / 30 categories covered**, 604 winner rationales generated, formal calibration on Outdoor + PR (75% binary on PR) |
| **6. Productization** | Reference React frontend with the oracle design system. PDF support. Multi-stage Dockerfile. Documentation. Handoff to deploy team | Deploy-ready container, end-to-end verified |

---

## By the numbers

| Metric | Value |
|---|---|
| Categories covered | 30 / 30 (full 2026 Cannes Lions entry catalogue) |
| Reference boards extracted | 1,466 |
| Winner rationales generated | 604 |
| Outdoor formal calibration | 80% binary accuracy (medal vs no medal) |
| PR formal calibration | 75% binary accuracy |
| Average prediction latency | 45 seconds |
| Average cost per prediction | ~$2 (Anthropic + Voyage AI) |
| Total smoke tests (CI) | 25 |
| Image formats accepted | JPG · PNG · WEBP · AVIF · GIF · PDF |
| Max upload size | 25 MB (configurable to 50 MB) |

---

## What is novel

A few elements of the project that we can credibly claim are first-of-kind
in the AI-for-creative-industry space.

1. **Per-category jury simulation.** Most "AI scoring" tools apply a single
   generic model. We built thirty distinct rubrics, each calibrated to the
   real Cannes 2026 entry kit, with category-specific axis weights and
   native-to-category checks.

2. **Retrieval-grounded judgment.** The LLM is not allowed to reason in a
   vacuum: it must compare the new board to seven concrete references
   (five winners, two losers) retrieved by semantic similarity. The
   references appear in the prompt with their actual jury rationale. This
   keeps the model anchored to real Cannes-grade examples.

3. **Art-Director-validated mental model.** The judge prompt encodes a
   specific definition of Strategy ("the WHY: brand mission and insight")
   versus Execution ("the HOW: orchestration and craft") that was
   reviewed and corrected by an Artefact Senior Art Director.

4. **The presage system.** Three rule-based modifiers reflect observable
   Cannes biases (aesthetic boards win more, international brands win
   more, agencies inside major networks win more). They are surfaced to
   the user as "presages" rather than hidden adjustments, which is
   editorially consistent with the oracle metaphor and honest about the
   real selection forces in the industry.

5. **Subagent orchestration for dataset construction.** Building 30
   category-specific RAG indexes required reading and analysing 1,466
   boards. We did this with Claude Code subagents running in
   subscription mode, parallel orchestration, **zero per-call API
   spend** during dataset prep. The marginal cost of adding a 31st
   category is now hours of subagent time, not thousands of dollars.

---

## Limits we are honest about

- **Indicative, not deterministic.** The engine predicts within plus or
  minus one tier roughly 70% of the time on Outdoor. Exact-tier
  prediction is harder and lands closer to 30%. We display this as a
  `confidence` field on every prediction and the UI communicates results
  as oracle-style guidance, never as an authoritative jury verdict.

- **The judge compresses scores in the 65 to 85 band.** This is a known
  property of large language models when asked to score subjective work.
  Past 2026, a supervised ML layer on top of the LLM output could
  recover the missing 5 to 10 percentage points of accuracy. We
  documented this as a Phase 7 candidate, deferred until real-world
  usage signals demand it.

- **Calibration coverage.** Of the 30 categories, only Outdoor and PR
  were formally calibrated against held-out test sets. The other 28
  were smoke-tested end-to-end (the pipeline runs and produces sensible
  output) but their numerical accuracy is not yet measured.

---

## Where we go next

The engine itself is feature-complete and dockerised. The remaining
work is operational:

1. **Deploy to GCP Cloud Run** with Secret Manager for the two API keys,
   Cloud Armor in front for bot defence, and the daily evaluation cap
   set to protect the API budget against bot traffic.

2. **Public launch tied to Cannes Lions 2026** as an Artefact marketing
   moment. The "Mrs Airma · The Cannes Oracle" brand was designed for
   this.

3. **Post-launch:** extend the formal calibration to high-volume
   categories (Film, Design, Social, Innovation), and consider adding
   the supervised ML layer if accuracy plateaus matter to users.

---

## Contacts

- **Engine lead**: Etienne Roure (etienne.roure@artefact.com)
- **Reference docs in the repo**:
  - `README.md`: entry point, quick start
  - `INTEGRATION.md`: full developer integration guide
  - `DOCUMENTATION.md`: engineering history (French)
  - `HANDOFF.md`: deploy team brief
