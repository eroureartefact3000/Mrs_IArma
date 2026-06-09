# Category brief — Outdoor Lions

> Per-category specifics for Cannes Lions Outdoor: axis weights, sub-category landscape, judging emphasis. Self-contained, no references to other files.

---

## What Outdoor celebrates

The Outdoor Lions celebrate creativity experienced **out of home**. The work should:

- Engage in the field (real public space, not a digital screen in a vacuum)
- Leverage public spaces to communicate a message or immerse consumers in a brand experience
- Land in **a single glance** — outdoor doesn't get a second look

The Cannes Lions entry kit lists the primary criteria as: **idea, execution, and impact**. Strategy is implicit but less emphasised by the jury than in PR or Engagement categories — reflected in the axis weights below.

---

## Axis weights (use these for `weighted_score`)

| Axis | Weight | Why this weight in Outdoor |
|---|---|---|
| **Idea** | **0.35** | Outdoor lives or dies on a single glance — the idea has to land instantly, with no read-time. The biggest weight. |
| **Strategy** | **0.10** | Conserved as a sanity check (brand mission fit, insight veracity) but jurors don't grade Outdoor primarily on strategic depth. |
| **Execution** | **0.30** | Craft + placement + orchestration + amplification. The native-to-outdoor test (see below) goes here. |
| **Impact** | **0.25** | Reach + business + cultural footprint. Boards have very varying levels of evidence here. |

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
| Grand Prix | 90 – 100 | Category-defining work |
| Gold | 80 – 100 | Strong on 3-4 axes, at most one minor weakness |
| Silver | 65 – 80 | Solid but one or two clear weaknesses |
| Bronze | 50 – 65 | Competent but unremarkable, OR great idea hurt by weak proof |
| Shortlist | `n/a` band | Passed first jury cut but missed metal. Score honestly — `tier_consistency` will be `n/a` regardless. |
| Loser | `n/a` band | Failed even the first jury screening. Score honestly — `tier_consistency` will be `n/a`. |

---

## Sub-categories within Outdoor (entry kit 2026)

Cannes Lions splits Outdoor into 5 sub-sections. You don't need to assign one — but knowing them helps you sense-check whether a board is genuinely Outdoor:

| Section | What it covers |
|---|---|
| **A. Billboards: Sectors** | Classic 2D / static-digital billboards (roadsides, highways, transit sides) |
| **B. Posters: Sectors** | Classic sheet / static-digital posters for public spaces (supermarkets, malls, airports) |
| **C. Ambient & Experiential** | Non-standard OOH leveraging public spaces, objects, environments (special builds, transit, live events, immersive experiences, interactive screens) |
| **D. Innovation in Outdoor** | Pushing the boundaries of out-of-home media (standard sites, ambient outdoor, tech-driven OOH) |
| **E. Culture & Context** | Outdoor brought to life through cultural insights / regional context (local brand, challenger, single-market, social behaviour, humour, budget, purpose, disruption, cultural engagement) |

---

## Native-to-category check (Outdoor-specific)

Outdoor's signature failure mode: **work that isn't actually outdoor** disguised as outdoor.

Common offenders:
- A **Twitch live-stream activation** with a single posed photo of a chair in a stadium
- A **televised live event** repurposed as OOH via a single post-event photo
- A **PR campaign** that picked up some OOH placements as an afterthought
- A **case-film campaign** with no actual placement that does the heavy lifting

How to detect:
- Read the board's execution list. Does an OOH / billboard / public-space placement do real work, or is it cosmetic?
- Is the campaign's primary moment in the physical world, or on a screen?

When the work fails the native check, you should:
- In **Pass 2** of extraction: still extract normally, but the visual style description should reflect what you see
- In **Rationale**: **hard-cap Idea ≤ 60 and Execution ≤ 50** and call this out explicitly in the rationales and verdict.

Example phrasing for the verdict:

> *"Submitted to Outdoor but executed as a Twitch overlay stunt — the jury had nothing public-space to reward, and the idea couldn't survive the category's glance-test."*

---

## Patterns commonly seen in Outdoor winners

(For pattern-matching only — never copy these into output verbatim.)

| Pattern | Example reference winners |
|---|---|
| `media-as-product` | Pedigree "Adoptable" (GP), JCDecaux "Meet Marina Prieto" (Gold) |
| `everyday-object-transformation` | Anzen Health "855-HOW-TO-QUIT" (Silver), Heinz "Smack for Heinz" (Bronze) |
| `placement-IS-the-idea` | Sol Cement "Sightwalks" (Gold), Faber-Castell "Shot on Faber-Castell" (Silver) |
| `slogan-recontextualisation` | KitKat "Phone Break" (GP), Magnum "Find Your Summer" (GP/Gold/Bronze) |
| `sponsorship-inversion` | Consul "Clean Sponsorship" (Gold/Silver) |
| `competitor-wordplay-ambush` | Aldi "Aldidas" (Shortlist), Budweiser "Et le Buuuuud" (Bronze) |
| `environment-responsive-billboard` | Magnum "Find Your Summer" (sun-tracking), Megh Santoor (rain-activated) |

---

## Quick checklist before submitting a rationale for Outdoor

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
