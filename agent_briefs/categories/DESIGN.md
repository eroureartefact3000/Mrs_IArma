# Category brief — Design Lions

> Per-category specifics for Cannes Lions Design: axis weights, sub-category landscape, judging emphasis. Self-contained, no references to other files.

---

## What Design celebrates

The Design Lions celebrate **craft-defined creative work**. The board IS the work — there's no media campaign wrapping a film, the design IS the artefact being judged. The work should:

- Demonstrate **craft excellence** (typography, illustration, photography, composition, materiality)
- Solve a **specific visual problem** with a single unifying concept
- Hold together as a **system** when shown across multiple applications

The Cannes Lions entry kit lists the primary criteria as: **idea, execution (craft), and impact**. Execution is the dominant axis — reflected in the axis weights below.

---

## Axis weights (use these for `weighted_score`)

| Axis | Weight | Why this weight in Design |
|---|---|---|
| **Idea** | **0.25** | A unifying concept matters, but for Design the idea is in service of craft. |
| **Strategy** | **0.10** | Conserved as a sanity check (brand mission fit, brief-to-solution fit). |
| **Execution** | **0.45** | **The biggest weight.** Craft IS the category. Typography, layout, materiality, system coherence — this is where Design Lions are won. |
| **Impact** | **0.20** | Brand metric shifts, design-press pickup, cultural conversation. Design is often less measurable, so qualitative impact counts. |

Use these weights to compute `weighted_score` in the rationale step:

```
weighted_score = idea.score * 0.25
              + strategy.score * 0.10
              + execution.score * 0.45
              + impact.score   * 0.20
```

---

## Expected score range per tier

A weighted score landing in this band → `tier_consistency: "expected"`. Outside → `"above"` or `"below"`.

| Tier | Band | Notes |
|---|---|---|
| Grand Prix | 90 – 100 | Category-defining design work |
| Gold | 80 – 100 | Strong craft across multiple applications |
| Silver | 65 – 80 | Solid craft with one or two clear weaknesses |
| Bronze | 50 – 65 | Competent but unremarkable, OR strong concept hurt by uneven craft |
| Shortlist | `n/a` band | Passed first jury cut but missed metal |
| Loser | `n/a` band | Failed even the first jury screening |

---

## Sub-categories within Design (entry kit 2026)

Cannes Lions splits Design into 6 sub-sections. You don't need to assign one — but knowing them helps sense-check whether the work is genuinely Design:

| Section | What it covers |
|---|---|
| **A. Brand Identity** | Visual identity systems (creation or refresh) — logo + palette + typography + applications |
| **B. Packaging Design** | Consumer / luxury / craft / sustainable / structural packaging |
| **C. Communication Design** | Publication design, posters, editorial, art direction |
| **D. Spatial / Environmental Design** | Signage, wayfinding, retail, exhibition design |
| **E. Digital & Interactive Design** | UI/UX, digital products, motion graphics |
| **F. Design Craft** | Typography, illustration, art direction, copywriting in design |

---

## Native-to-category check (Design-specific)

Design's signature failure mode: **work that wasn't actually design** submitted to Design.

Common offenders:
- A **PR / publicity stunt** with a one-off poster designed for it (work is PR, not Design)
- A **case film** that summarises a design project — but the actual artefacts aren't the focus
- A **branding refresh** that mostly shows ads using the new logo (work is advertising, not Design)
- A **packaging tweak** with no system coherence — just one SKU

How to detect:
- The board should show **the design artefacts themselves** (logo construction, packaging mock-ups, signage in context, type specimens)
- Look for **system extensibility** — does the work hold across multiple applications, or is it a one-off?
- Is the **craft visible** at the scale of the board? Typography choices, composition discipline, colour decisions should read on the page.

When the work fails the native check, you should:
- In **extraction**: still extract normally
- In **Rationale**: **hard-cap Idea ≤ 60 and Execution ≤ 50** and call this out explicitly in the rationales and verdict.

Example phrasing for the verdict:

> *"Submitted to Design but executed as a publicity stunt with a single designed asset — the jury had little design-system craft to reward across applications."*

---

## Patterns commonly seen in Design winners

(For pattern-matching only — never copy these into output verbatim.)

| Pattern | What it looks like |
|---|---|
| `identity-system-redesign` | New logo + palette + typography + application grid showing the system in use |
| `cultural-heritage-codified` | Design system built around regional / cultural visual codes (motifs, scripts, materials) |
| `inclusive-design-system` | Identity / typeface designed for under-represented groups (Code My Crown, Maqroo Arabic dyslexia font) |
| `packaging-as-ritual` | Packaging structure that creates a unique unboxing or use ritual |
| `signage-as-narrative` | Environmental design where wayfinding is also storytelling |
| `craft-as-the-point` | The artefact itself is the entire creative idea — typography, illustration, or art-direction craft IS the concept |
| `purpose-driven-identity` | Visual system carrying a social / environmental cause (recycle codes, advocacy posters) |

---

## Quick checklist before submitting a rationale for Design

- [ ] Strategy stays strictly WHY (brand mission fit, brief-to-solution fit) — no craft leaking in
- [ ] Execution stays strictly HOW (craft, system coherence, production) — no brand mission leaking in
- [ ] Native-to-category check applied (if the work is really PR / advertising, hard-cap Idea/Execution)
- [ ] System coherence assessed across applications (if relevant)
- [ ] All percentages have a "of what?" check (RIGOUR pattern 1)
- [ ] Press claims framed as entrant-reported (RIGOUR pattern 2)
- [ ] Real business outcome OR cultural-impact evidence assessed (RIGOUR pattern 3)
- [ ] No vague superlatives without an immediate concrete justification (RIGOUR pattern 4)
- [ ] Cultural / linguistic scope named precisely when relevant (RIGOUR pattern 5)
- [ ] Synthesis-style fields are observational, never advisory (no imperative verbs)
- [ ] Weighted score = 0.25·Idea + 0.10·Strategy + 0.45·Execution + 0.20·Impact
- [ ] `tier_consistency` set honestly based on whether weighted score lands in the band
