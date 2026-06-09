# Category brief — PR Lions

> Per-category specifics for Cannes Lions PR: axis weights, sub-category landscape, judging emphasis. Self-contained, no references to other files.

---

## What PR celebrates

The PR Lions celebrate the craft of **strategic and creative communication**. The work should demonstrate how:

- **Original thinking** and **transformative insight**
- A strategy **rooted in earned media** (not paid-first)
- Have **influenced opinion** and **driven progress and change** in business, society, or culture

PR work has **storytelling at its core** and aims to **establish, protect, and enhance** the reputation and business of an organisation or brand. The category is dominated by campaigns that "earn" their attention — through press relations, cultural moments, social conversation, partnerships, events — rather than buying it.

---

## Axis weights (use these for `weighted_score`)

| Axis | Weight | Why this weight in PR |
|---|---|---|
| **Idea** | **0.20** | A great idea matters, but in PR the strategic angle and the earned outcome carry more weight than pure originality. |
| **Strategy** | **0.30** | The biggest weight. PR is fundamentally a strategic discipline — earned-media-first thinking, data-rooted insight, audience targeting, alignment with brand mission. |
| **Execution** | **0.20** | Quality and creativity of the implementation: media relations, stunts, events, partnerships, real-time response, influencer marketing. |
| **Impact** | **0.30** | Tied for biggest weight. PR is judged heavily on measurable outcomes: business results AND quality/quantity of earned coverage. |

Use these weights to compute `weighted_score`:

```
weighted_score = idea.score * 0.20
              + strategy.score * 0.30
              + execution.score * 0.20
              + impact.score   * 0.30
```

---

## Expected score range per tier

A weighted score landing in this band → `tier_consistency: "expected"`. Outside the band → `"above"` or `"below"`.

| Tier | Band | Notes |
|---|---|---|
| Grand Prix | 90 – 100 | Category-defining PR work |
| Gold | 80 – 100 | Strong on 3-4 axes, at most one minor weakness |
| Silver | 65 – 80 | Solid but one or two clear weaknesses |
| Bronze | 50 – 65 | Competent but unremarkable, OR great idea hurt by weak proof |
| Shortlist | `n/a` band | Passed first jury cut but missed metal. Score honestly — `tier_consistency` will be `n/a` regardless. |
| Loser | `n/a` band | Failed even the first jury screening. Score honestly — `tier_consistency` will be `n/a`. |

---

## Sub-categories within PR (entry kit 2026)

Cannes Lions splits PR into 6 sub-sections. You don't need to assign one — but knowing them helps you sense-check whether a board is genuinely PR:

| Section | What it covers |
|---|---|
| **A. PR: Sectors** | Sector-based entries (Consumer Goods, Healthcare, Automotive, Travel/Leisure/Retail, Media/Entertainment, B2B, NFP/Charity/Government) |
| **B. Social Engagement & Influencer Marketing** | Social-platform-led PR (community management, real-time response, content amplification, influencer-driven brand work) |
| **C. Insights & Measurement** | Research-led PR, PR effectiveness — data-rooted communications strategies |
| **D. PR Techniques** | The technique itself is the highlight: media relations, events/stunts, launches/relaunches, brand-voice storytelling, use of tech, employee engagement |
| **E. Excellence in PR Craft** | Independent PR agencies only — corporate image, public affairs/lobbying, crisis comms, internal comms, sponsorship |
| **F. Culture & Context** | Cultural insight-driven PR (local brand, challenger, single-market, social behaviour, humour, budget, purpose, market disruption, cultural engagement) |

---

## Native-to-category check (PR-specific)

PR's signature failure mode: **work that wasn't actually earned**.

Common offenders:
- A paid-media campaign with a few press logos slapped at the bottom of the board
- A product launch with no real PR strategy — just a press release sent into the void
- An influencer-only campaign that's really paid social, not earned conversation
- A film/video campaign that picked up press as an afterthought, not by design

How to detect:
- Did the campaign **earn** its press, or **buy** it? Look for cultural-conversation evidence, real-time response moments, partnership leverage, audience-driven amplification.
- Is the impact measured in earned-media terms (press pickup, sentiment shift, share of voice) or only in paid-media terms (reach, impressions from paid placements)?
- Is the idea built around an earned-media hook (a stunt, a partnership, a cultural moment) or around a polished asset?

When the work fails the native check, you should:
- In Pass 2 of extraction: still extract normally, but the visual style description should reflect what you see
- In Rationale: hard-cap Idea ≤ 60 and Execution ≤ 50 and call this out explicitly in the rationales and verdict.

Example phrasing for a failed native check:

> *"Submitted to PR but executed as a paid-media campaign with token press logos — earned-media engine missing, so the jury had little to reward on the strategic axis."*

---

## Patterns commonly seen in PR winners

(For pattern-matching only — never copy these into output verbatim.)

| Pattern | Reference examples |
|---|---|
| `cultural-conversation-hijack` | Brands inserting themselves into a high-traffic cultural moment (sports finals, political moments, viral events) |
| `data-driven-newsmaking` | Original research / data that generates earned coverage on its own |
| `brand-as-activist` | Brand takes a public stance on a social issue and drives press + legislative discussion |
| `partnership-as-news` | Surprising or category-busting partnership between brands or with NGOs/government |
| `everyday-object-transformation` | Common physical object reframed to generate press attention (Indian Railways "Lucky Yatra" — ticket as lottery ticket) |
| `legislative-advocacy` | Campaign explicitly designed to move a law / regulation (UN Women "Child Wedding Cards") |
| `victim-as-author` | A campaign whose voice is the affected community itself, not the brand speaking on their behalf |
| `crisis-reframe` | Turning a brand crisis into a reputation-building moment |
| `purpose-driven-campaign` | Long-term brand purpose translated into a specific PR moment (Dove "Real Beauty", P&G "#ShareTheLoad") |

---

## Quick checklist before submitting a rationale for PR

- [ ] Strategy stays strictly WHY (no channels / orchestration leaking in)
- [ ] Execution stays strictly HOW (no brand mission leaking in)
- [ ] Native-to-category check applied (if it fails, hard-cap Idea/Execution)
- [ ] All percentages have a "of what?" check (RIGOUR pattern 1)
- [ ] Press claims framed as entrant-reported (RIGOUR pattern 2)
- [ ] Real business outcome assessed (RIGOUR pattern 3)
- [ ] No vague superlatives without an immediate concrete justification (RIGOUR pattern 4)
- [ ] Cultural / linguistic scope named precisely when relevant (RIGOUR pattern 5)
- [ ] Synthesis-style fields are observational, never advisory (no imperative verbs)
- [ ] Weighted score = 0.20·Idea + 0.30·Strategy + 0.20·Execution + 0.30·Impact
- [ ] `tier_consistency` set honestly based on whether weighted score lands in the band
