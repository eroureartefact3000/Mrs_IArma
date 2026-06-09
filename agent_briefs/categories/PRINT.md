# Category brief — Print & Publishing Lions

> Per-category specifics for Cannes Lions Print & Publishing: axis weights, sub-category landscape, judging emphasis. Self-contained, no references to other files.

---

## What Print & Publishing celebrates

The Print & Publishing Lions celebrate creative work in **print media** — newspapers, magazines, publications, in-store print, branded content. The work should:

- Work in a **single page or spread** — headline + hero image + minimal copy
- Land **without long body copy** — the page is the medium
- Showcase craft of typography, photography, illustration, art direction

The Cannes Lions entry kit lists the primary criteria as: **idea, execution, and impact**. Strategy is implicit but less emphasised by the jury than in PR or Engagement categories — reflected in the axis weights below (same family as Outdoor).

---

## Axis weights (use these for `weighted_score`)

| Axis | Weight | Why this weight in Print |
|---|---|---|
| **Idea** | **0.35** | Print is idea-led: a great headline + visual lands in one glance. The biggest weight. |
| **Strategy** | **0.10** | Conserved as a sanity check (brand mission fit, insight veracity) but jurors don't grade Print primarily on strategic depth. |
| **Execution** | **0.30** | Craft + publication placement + multi-execution coherence. Typography and art-direction quality go here. |
| **Impact** | **0.25** | Reach + business + cultural footprint. Print boards often have lighter impact evidence than digital. |

Use these weights to compute `weighted_score` in the rationale step:

```
weighted_score = idea.score * 0.35
              + strategy.score * 0.10
              + execution.score * 0.30
              + impact.score   * 0.25
```

---

## Expected score range per tier

A weighted score landing in this band → `tier_consistency: "expected"`. Outside the band → `"above"` or `"below"`.

| Tier | Band | Notes |
|---|---|---|
| Grand Prix | 90 – 100 | Category-defining print work |
| Gold | 80 – 100 | Strong on 3-4 axes, at most one minor weakness |
| Silver | 65 – 80 | Solid but one or two clear weaknesses |
| Bronze | 50 – 65 | Competent but unremarkable, OR great idea hurt by weak proof |
| Shortlist | `n/a` band | Passed first jury cut but missed metal. Score honestly — `tier_consistency` will be `n/a` regardless. |
| Loser | `n/a` band | Failed even the first jury screening. Score honestly — `tier_consistency` will be `n/a`. |

---

## Sub-categories within Print & Publishing (entry kit 2026)

Cannes Lions splits Print & Publishing into 5 sub-sections. You don't need to assign one — but knowing them helps you sense-check whether a board is genuinely Print:

| Section | What it covers |
|---|---|
| **A. Press & Publications: Sectors** | Sector-based entries in newspapers/magazines (Consumer Goods, Healthcare, Automotive, Travel/Leisure/Retail, Media/Entertainment, B2B, NFP/Charity/Government) |
| **B. Direct Print** | Direct mail, branded content in print, in-store / point-of-sale print |
| **C. Innovation in Print** | Pushing the boundaries of print media (standard sites, ambient print, technology in print) |
| **D. Print Craft** | Typography, illustration, photography, art direction, copywriting in print |
| **E. Culture & Context** | Print brought to life through cultural insights (local brand, challenger, single-market, social behaviour, humour, budget, purpose, disruption, cultural engagement) |

---

## Native-to-category check (Print-specific)

Print's signature failure mode: **work that wasn't actually print** disguised as a print campaign.

Common offenders:
- A **digital banner campaign** with a static screenshot styled like a magazine page
- An **OOH billboard** repurposed as a "press ad" with no actual newspaper / magazine placement
- A **case-film campaign** with no real print medium doing the heavy lifting
- A **packaging design** entered as print when the work is really brand identity

How to detect:
- Look for actual **publication placement** evidence on the board: newspaper / magazine logos, page mock-ups, in-publication photography
- Read the execution list: does a print insertion do real work, or is it cosmetic?
- Is the idea genuinely **single-frame** (works as a static page), or is it really a film / digital story compressed into one image?

When the work fails the native check, you should:
- In **Pass 2** of extraction: still extract normally, but the visual style description should reflect what you see
- In **Rationale**: **hard-cap Idea ≤ 60 and Execution ≤ 50** and call this out explicitly in the rationales and verdict.

Example phrasing for the verdict:

> *"Submitted to Print but executed as a packaging system with magazine-style mock-ups — no real publication placement does the work, so the jury had little native-print to reward."*

---

## Patterns commonly seen in Print winners

(For pattern-matching only — never copy these into output verbatim.)

| Pattern | What it looks like |
|---|---|
| `headline-visual-twist` | Headline that flips meaning of the hero image (Stella Artois "World's Most Famous Hand Model") |
| `brand-icon-recontextualisation` | The brand's iconic visual asset placed in an unexpected context (Coca-Cola "Recycle Me" — distorted bottle silhouettes as recycling encouragement) |
| `visual-pun-or-mnemonic` | Image-as-pun where the visual carries the whole gag (Magnum "Find Your Summer") |
| `cultural-iconography-co-opted` | Heritage / historical visual codes re-anchored on the brand (L'Oréal "Braided History") |
| `editorial-print-takeover` | Special edition / front-page wrap of an actual publication |
| `craft-as-the-point` | Typography, illustration, or art-direction craft IS the idea (Penguin Random House illustrated covers) |
| `purpose-driven-poster` | Heavy social or environmental message landed in a single page |

---

## Quick checklist before submitting a rationale for Print

- [ ] Strategy stays strictly WHY (no channels / orchestration leaking in)
- [ ] Execution stays strictly HOW (no brand mission leaking in)
- [ ] Native-to-category check applied (if it fails, hard-cap Idea/Execution)
- [ ] All percentages have a "of what?" check (RIGOUR pattern 1)
- [ ] Press claims framed as entrant-reported (RIGOUR pattern 2)
- [ ] Real business outcome assessed (RIGOUR pattern 3)
- [ ] No vague superlatives without an immediate concrete justification (RIGOUR pattern 4)
- [ ] Cultural / linguistic scope named precisely when relevant (RIGOUR pattern 5)
- [ ] Synthesis-style fields are observational, never advisory (no imperative verbs)
- [ ] Weighted score = 0.35·Idea + 0.10·Strategy + 0.30·Execution + 0.25·Impact
- [ ] `tier_consistency` set honestly based on whether weighted score lands in the band
