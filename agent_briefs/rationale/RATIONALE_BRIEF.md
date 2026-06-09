# Rationale brief — "Why this board won its tier"

> Procedure for rationale generation: for each board that already has a known Cannes Lions tier, produce a structured "why it won" analysis used to populate the RAG index. Self-contained, no references to other files.

---

## What rationale does

For each (known-winner) board in your batch:

1. Read the existing finalised extraction at `data_internal/extractions/<category>/<slug>.json` (do **not** re-read the image — work from the structured extraction only)
2. Build a per-axis rationale and tier-consistent score for each of the 4 axes (Idea / Strategy / Execution / Impact)
3. Compose a 1-sentence verdict explaining the single biggest reason this board got its tier
4. Compute the `weighted_score` from per-axis scores using the category's official weights (supplied in your task brief)
5. Set `tier_consistency` based on whether the weighted score lands in the expected band for that tier (supplied in your task brief)
6. Write the result to `data_internal/rationales/<category>/<slug>.json`

> **Important**: rationale subagents do NOT predict tiers. The tier is already known (it's in `extracted.tier`). Your job is to **explain retrospectively** why the jury awarded that tier — not to second-guess it.

---

## Output schema

```json
{
  "id": "<slug, same as extraction>",
  "tier": "<tier, same as extraction>",
  "category": "<category, same as extraction>",
  "axes": {
    "idea":      { "score": <int 0-100>, "rationale": "<2-3 sentences>" },
    "strategy":  { "score": <int 0-100>, "rationale": "<2-3 sentences, WHO + mission-fit + insight-veracity>" },
    "execution": { "score": <int 0-100>, "rationale": "<2-3 sentences, orchestration + media-target fit>" },
    "impact":    { "score": <int 0-100>, "rationale": "<2-3 sentences, RIGOUR-applied>" }
  },
  "weighted_score": <float, sum of (axis.score * axis.weight) for the 4 axes>,
  "tier_consistency": "expected | below | above | n/a",
  "verdict": "<1-2 sentences naming THE single biggest reason this got its tier>"
}
```

---

## Procedure for one board

### Step 1 — Read the extraction

```python
# pseudo-code, conceptual:
rec = read_json(f"data_internal/extractions/{category}/{slug}.json")
extracted   = rec["extracted"]
inferred    = rec["inferred"]
visual      = rec["visual"]
known_tier  = rec["tier"]   # ← the ground truth you are explaining
```

### Step 2 — Apply the DA mental model

The DA model is **strict**:

- **Strategy = WHY** — answer in this order:
  1. **WHO IS THE BRAND?** Identify the brand and its mission. If the brand is not internationally known, name what it stands for.
  2. Is the idea coherent with that brand's mission?
  3. Are the context and insights real, verifiable, data-backed? Cite specific data points from the board.

  Do **NOT** discuss orchestration / channels / media choices / amplification in the Strategy rationale. Those belong to Execution.

- **Execution = HOW** — answer:
  - Are the means and media chosen relevant to the objective and the target?
  - What were the phases of the campaign? Which channels? Amplification layers?

  Do **NOT** discuss brand mission, insight quality, or context veracity in the Execution rationale. Those belong to Strategy.

### Step 3 — Apply the 5 RIGOUR patterns

The 5 RIGOUR patterns (percentages without base, unverified press, missing business outcome, no vague superlatives, cultural/linguistic precision) are non-negotiable. Apply them in every rationale. The full list is provided to you as part of the briefing material.

### Step 4 — Score each axis

For each axis (Idea, Strategy, Execution, Impact):
- Score 0-100 on absolute craft, not relative to the tier
- The 4 axes' weighted average should land in the band expected for the known tier (the expected band per tier is supplied in your task brief)
- If your honest assessment of the 4 axes produces a weighted score outside the tier's band, do NOT cheat the scores to fit. Set `tier_consistency` accordingly:
  - `"expected"` — weighted score lands in the band for the known tier
  - `"above"` — weighted score is higher than the band's upper bound (jury was harsher than your read)
  - `"below"` — weighted score is lower than the band's lower bound (jury was kinder than your read)
  - `"n/a"` — for `Shortlist` and `Loser` records (no medal band defined)

Most rationales will be `"expected"`. Some will diverge — that's information, not failure.

### Step 5 — Write the verdict

A single sentence (occasionally two) explaining **the** single deciding factor. The verdict is what a juror would write at the top of their deliberation note.

Good examples:
- *"Wins the Grand Prix because it rebuilds the entire brand media buy into an adoption product, not just an ad."*
- *"Lands Silver because the imprint-code-as-extension is genuinely original and on-brief, but the impact case rests on unbased percentages."*
- *"Bronze because the ambush is clever and credibly Québec-specific, but the joke is regional and the metrics are unanchored."*

Bad examples (avoid):
- *"A brilliant, exceptional campaign that wowed the jury."* — vague superlative
- *"This board has many strengths and some weaknesses."* — non-information
- *"You should add more metrics to climb higher."* — advisory / forward-looking (boards have already been submitted, synthesis is post-mortem only)

### Step 6 — Compute weighted score

```
weighted_score = (idea.score   * idea_weight)
              + (strategy.score * strategy_weight)
              + (execution.score * execution_weight)
              + (impact.score    * impact_weight)
```

Axis weights are supplied in your task brief (e.g. Outdoor = 35/10/30/25, PR = 20/30/20/30).

### Step 7 — Write the file

Write to `data_internal/rationales/<category>/<slug>.json`. Validate the JSON against the schema first; do not overwrite existing files.

---

## Worked example — Pedigree "Adoptable" (Grand Prix, Outdoor)

Given the extraction at `extractions/outdoor/adoptable-pedigree-colenso-bbdo-auckland.json` for the Pedigree "Adoptable" board (Grand Prix), here is the rationale output:

```json
{
  "id": "adoptable-pedigree-colenso-bbdo-auckland",
  "tier": "Grand Prix",
  "category": "Outdoor",
  "axes": {
    "idea": {
      "score": 95,
      "rationale": "Reframing every brand media impression as a working ad for a real, locally-available adoptable dog is a category-redefining reframe of media itself as the product. It lands instantly on a billboard with just a name ('Meet Candy') and a face — natively outdoor rather than a film compressed into a poster."
    },
    "strategy": {
      "score": 92,
      "rationale": "Pedigree is Mars's global dog-food brand whose long-running 'Feed the Good' / 'Dogs Rule' mission has anchored shelter-adoption advocacy for two decades, so converting paid media into an adoption engine is exact mission-fit, not borrowed purpose. The insight — shelter dogs are overlooked because their photos look amateur next to polished brand imagery — is a plain, observable cultural truth the AI 'glow-up' directly attacks. The board cites the insight as self-evident rather than backing it with adoption-rate data, which is the only soft spot."
    },
    "execution": {
      "score": 93,
      "rationale": "The bespoke AI restoration + CGI repose pipeline lets a single shelter snapshot land in any Pedigree creative, delivered as geo-targeted DOOH near each dog's actual shelter with QR-to-meet handoff and auto-removal on adoption. The orchestration closes the loop from billboard impression to shelter visit to adoption, and the yellow-poster system keeps multi-execution coherence across hundreds of unique dogs."
    },
    "impact": {
      "score": 85,
      "rationale": "The headline behaviour-change number — '50% of featured dogs adopted within two weeks' — is the right business outcome for an adoption campaign, though the cohort size isn't disclosed on the board, so '50% of how many dogs?' remains open. The 6x lift in shelter site visits is a credible directional proxy. The '100% purpose-led media investment by 2026' is a commitment rather than a result, but it signals durable cultural footprint beyond the campaign window."
    }
  },
  "weighted_score": 91.85,
  "tier_consistency": "expected",
  "verdict": "Wins the Grand Prix because it rebuilds the entire brand media buy into an adoption product — each impression tied to a specific, local, adoptable dog that disappears the moment she finds a home."
}
```

Notice:
- **Strategy** answers WHO IS THE BRAND first ("Pedigree is Mars's global dog-food brand…"), then mission-fit, then insight-veracity. Zero discussion of channels / orchestration.
- **Execution** discusses the AI pipeline + DOOH + QR + auto-removal — pure HOW. Zero discussion of brand purpose.
- **Impact** applies RIGOUR: notes the unbased "50%", credits the 6x as a "directional proxy" (not a hard outcome), separates "commitment" from "result".
- **Verdict** names THE single deciding factor — the media-as-product reframe.
- Weighted score: 95×0.35 + 92×0.10 + 93×0.30 + 85×0.25 = 91.85 → lands in the Grand Prix band (90-100) → `tier_consistency: "expected"`.

---

## Reporting your batch

```
RATIONALE SUMMARY
=================
Boards processed: 24
  ✓ written:     23
  ↻ skipped:     1 ([slug] already done)
  ✗ errors:      0

Tier consistency breakdown:
  expected:  19
  above:      2
  below:      2
  n/a:        0
```

Return this summary in your final message. Do not write it to disk.
