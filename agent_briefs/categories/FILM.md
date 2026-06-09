# Category brief — Film Lions

> **Signal caveat**: Film is a video-first category. The board is a CASE STUDY of the film, not the film itself. Extract carefully from keyframes + tagline + production credits. Self-contained.

---

## What Film celebrates

Creative work delivered through **moving image** — TV spots, online films, branded shorts, feature-length brand content. The judging targets the **film itself**; the board is the jury's window into it.

**Extraction note**: read keyframes / storyboard tiles, tagline, brief, and production credits from the board. Do not invent details about the film that aren't visible — flag the board if the actual film artefact is required but only a poster-style case board is provided.

---

## Axis weights

| Axis | Weight |
|---|---|
| **Idea** | **0.35** |
| **Strategy** | **0.10** |
| **Execution** | **0.35** |
| **Impact** | **0.20** |

```
weighted_score = idea.score * 0.35 + strategy.score * 0.10
              + execution.score * 0.35 + impact.score * 0.20
```

---

## Tier bands

| Tier | Band |
|---|---|
| Grand Prix | 90 – 100 |
| Gold | 80 – 100 |
| Silver | 65 – 80 |
| Bronze | 50 – 65 |

---

## Sub-categories (entry kit 2026)

| Section | What it covers |
|---|---|
| **A. Film: Sectors** | TV / online films by sector |
| **B. Use of Channels** | TV, Online, Cinema, Social-First, Branded Content |
| **C. Excellence in Film** | Single-Market, Use of Tech, Budget |
| **D. Culture & Context** | Local, Challenger, Behaviour, Humour, Budget, Purpose, Disruption |

---

## Native-to-category check

Film's failure mode (for OUR extraction system): **the case board doesn't show the film**, just a tagline + a single hero still.

When extracting, if the board lacks visible film evidence (storyboard, keyframes, multiple stills), set `review_flag: true` with reason "Film not represented on board — extraction limited to case-study summary". Still extract whatever's visible.

Common Film-category creative failure modes:
- **Print-style execution** dressed as film (just a tagline + product shot, repeated)
- **Stock-footage assembly** with no original cinematography
- **A PR-led campaign** that has a film component but no real film craft
- **Workmanlike storytelling** with no memorable visual or narrative hook

When the work fails the native check:
- Hard-cap Idea ≤ 60 and Execution ≤ 50 in the rationale.

Example phrasing:

> *"Submitted to Film but the board shows only a tagline + hero still — without film evidence, the jury had no actual film craft to reward."*

---

## Patterns in Film winners

| Pattern | What it looks like |
|---|---|
| `narrative-twist` | Short film with a single sharp reveal at the end |
| `documentary-truth` | Real people, real moments — earned-attention storytelling |
| `cinematography-as-the-idea` | The look of the film IS the message (Apple Shot On iPhone) |
| `cultural-icon-narrative` | Famous person / brand mascot fronting a story |
| `purpose-led-emotion` | Emotional story carrying a brand purpose message |
| `humour-driven-campaign` | Genuinely funny film, character-led, repeat-watchable |
| `epic-scale-production` | Long-form ambitious production (Apple, Nike, John Lewis-tier) |

---

## Checklist

- [ ] Note in extraction notes if the board lacks film evidence
- [ ] Strategy stays strictly WHY
- [ ] Execution stays strictly HOW (craft inferred from keyframes + credits)
- [ ] Native check applied
- [ ] Production credits noted in Execution rationale when visible
- [ ] RIGOUR patterns 1-5 applied
- [ ] Synthesis observational
- [ ] Weighted score = 0.35·Idea + 0.10·Strategy + 0.35·Execution + 0.20·Impact
