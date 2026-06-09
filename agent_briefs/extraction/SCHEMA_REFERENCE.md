# Extraction schema (v3)

> The exact JSON shape an extraction output must match. With 3 worked examples and notes on common traps. Self-contained, no references to other files.

The schema is enforced by Pydantic. Field names must match exactly — do not rename or reorder.

---

## Top-level shape

A complete extraction record (Pass 1 + Pass 2 combined, written to `data_internal/extractions/<cat>/<slug>.json`):

```json
{
  "id": "<slug>",
  "tier": "Grand Prix | Gold | Silver | Bronze | Shortlist | Loser",
  "category": "<exact Cannes Lions category name, e.g. 'Outdoor'>",
  "file_path": "<path of the source image, relative to repo root>",

  "extracted": { ... },        // Pass 1 — strict, literal only
  "inferred": { ... },         // Pass 2 — fills missing Pass 1 fields when confident
  "visual": { ... },           // Pass 2 — always required

  "review_flag": false,        // true if you produced a record but want a human to double-check
  "review_reasons": []
}
```

Notes:
- `tier`, `category`, and `file_path` come from your task brief. Do not re-derive them.
- `review_flag` is **only** for marginal cases where you produced a record but want a human to verify. For truly unusable boards, use the flag mechanism (write to `flagged/`) instead — don't produce an extraction.

---

## `extracted` (Pass 1)

```json
"extracted": {
  "campaign": "string or null",
  "brand": "string or null",
  "agencies": [],                       // always [] (agencies are in filenames, not on boards)
  "tagline": "string or null",
  "context": "string or null",          // max ~300 chars
  "insight": "string or null",
  "idea": "string or null",
  "execution": [],                      // list of short bullets — see Pass 1 rules below
  "metrics": [],                        // list of strings like "$685M revenue" — unit + number
  "press_coverage": []                  // list of outlet names or short quotes
}
```

### Field-by-field

| Field | What it is | When `null` is correct |
|---|---|---|
| `campaign` | Campaign name as printed on the board (often the big title) | When no title is visible or the title is purely visual (a logo with no readable name) |
| `brand` | The brand / advertiser | When the brand is only inferable from context — Pass 2 may fill it |
| `agencies` | **Always an empty list**. Agencies are in filenames, not on boards. Do not try to extract. | N/A |
| `tagline` | The headline/sub-headline at the top of the board | When the board's top text is the campaign name only |
| `context` | The problem / challenge / background, as written | When no explicit problem statement is present |
| `insight` | The consumer / cultural insight, as written | When no explicit insight statement is present |
| `idea` | The core creative idea, in 1-2 sentences | When the idea is implied but not stated in text |
| `execution` | Channels / mechanics / executions. Bullet points. | List can include items shown in an **unambiguous visual strip** (OOH photos, gameplay shots, app screens). Leave `[]` only when nothing of the execution is shown. |
| `metrics` | Quantified results with unit + number ("34% increase in sales", "$685M revenue"). Drop numbers whose unit is unreadable. | `[]` when no readable quantified results |
| `press_coverage` | Outlet names visible (logos) or short journalist quotes | `[]` when no press logos / quotes |

### Pass 1 rules recap

- A field is `null` (or `[]` for lists) when **not literally visible**
- Paraphrase tightly when text is long
- Output language is **English** — paraphrase non-English text into English
- For `metrics`: always include the unit ("$685M", "34%", "560M impressions"). A bare number is useless.

---

## `inferred` (Pass 2)

```json
"inferred": {
  "context": "string or null",         // null if extracted.context is already filled
  "insight": "string or null",         // null if extracted.insight is already filled
  "idea": "string or null",            // null if extracted.idea is already filled
  "one_liner": "string",               // always required — the punchy headline-style sentence
  "creative_mechanisms": [],           // 3-5 kebab-case English tags
  "qualitative_summary": "string"      // 1-2 sentence narrative of impact
}
```

### Field-by-field

| Field | What it is | Notes |
|---|---|---|
| `context`, `insight`, `idea` | Inferred only when the corresponding `extracted.*` is `null`. Otherwise `null` here. | Confidence threshold: infer only if the visuals + other extracted fields make the inference defensible. Otherwise leave `null` (the orchestrator will decide what to do). |
| `one_liner` | Always required. The single most memorable sentence summarising the idea. | Max 12 words. Imitate the style: "The train ticket IS the lottery ticket.", "The pill becomes the helpline.", "Every Pedigree ad dog is a real shelter dog." |
| `creative_mechanisms` | 3-5 tags identifying the creative move | See rule 10. Always English kebab-case, 2-5 words. |
| `qualitative_summary` | A short narrative of impact (cultural, behavioural, business). Always required. | 1-2 sentences max. |

### `one_liner` guardrails (hard requirements)

- **≤ 12 words**
- No gerunds, no participial phrases at the start ("turning", "making", "letting")
- No mention of metric numbers (the metric belongs in the `metrics` list)
- Prefer `"X IS Y"`, `"X becomes Y"`, `"<noun phrase>"` patterns

### Common good `creative_mechanisms` tags (non-exhaustive)

- `everyday-object-transformation`
- `celebrity-as-prop`
- `ambient-media-hijack`
- `platform-jailbreak`
- `data-as-content`
- `ritual-creation`
- `cultural-symbol-subversion`
- `purpose-driven-product`
- `algorithm-hijack`
- `name-as-content`
- `rights-circumvention`
- `slogan-recontextualisation`
- `direct-mail-confrontation`
- `legislative-advocacy`
- `media-as-product`

Invent new ones when none of the above fits — but keep the kebab-case convention.

---

## `visual` (Pass 2)

```json
"visual": {
  "style_description": "string",                 // 1-2 sentences
  "craft_quality": "high | medium | low",
  "dominant_colors": ["string", ...]             // 2-4 plain colour names
}
```

### Field-by-field

| Field | What it is | Notes |
|---|---|---|
| `style_description` | Composition style in 1-2 sentences | "Photo-led case board with a dark crowd backdrop and red callout blocks; dense info-graphic layout." |
| `craft_quality` | One of three labels | `high` = polished, award-grade craft; `medium` = clean professional but not exceptional; `low` = amateur, rushed, weak typography/layout |
| `dominant_colors` | 2-4 dominant colours, plain English | `["red", "black", "white"]`, `["beige", "navy", "ochre"]`. Avoid hex codes. |

---

## Final impact check before finalizing

Before writing the record, verify the board carries at least some impact signal:

- `extracted.metrics` has ≥ 1 entry, OR
- `extracted.press_coverage` has ≥ 1 entry, OR
- `inferred.qualitative_summary` is a meaningful 1-2 sentence outcome narrative

If **none** of these is true, do **not** write the extraction — flag the board instead. A board with no impact evidence at all is almost certainly unreadable or off-topic.

(Note: the engine computes an internal "impact strength" label at runtime from these same signals; it does not need to be stored in the JSON.)

---

## Three worked examples (real boards, real outputs)

These show the shape end-to-end for three reference cases. Use them as your mental template.

### Example A — Pedigree "Adoptable" (Grand Prix, dense narrative + metrics)

```json
{
  "id": "adoptable-pedigree-colenso-bbdo-auckland",
  "tier": "Grand Prix",
  "category": "Outdoor",
  "file_path": "2024/OUTDOOR/GRAND PRIX/Adoptable - Pedigree (Colenso BBDO, Auckland).webp",

  "extracted": {
    "campaign": "Adoptable",
    "brand": "Pedigree",
    "agencies": [],
    "tagline": "Every Pedigree ad is now an ad for a real shelter dog near you.",
    "context": "Shelter dogs are overlooked because their photos can't compete with polished brand imagery.",
    "insight": "If a shelter dog can be shown in Pedigree-quality imagery, more people will adopt.",
    "idea": "AI restores shelter dog photos to brand-grade quality; CGI re-poses them into Pedigree creatives; each ad is geo-targeted near the dog's actual shelter.",
    "execution": [
      "AI 'glow-up' pipeline restores amateur shelter photos to brand-grade quality",
      "CGI rig re-poses the same dog into any Pedigree creative",
      "Geo-targeted DOOH near each dog's actual shelter",
      "QR code on the ad opens the dog's mobile profile",
      "Ad auto-removed the moment the dog is adopted"
    ],
    "metrics": [
      "6x increase in shelter site visits",
      "50% of featured dogs adopted within two weeks",
      "Commitment to 100% purpose-led media investment by 2026"
    ],
    "press_coverage": ["Adweek", "Campaign", "Fast Company"]
  },

  "inferred": {
    "context": null,
    "insight": null,
    "idea": null,
    "one_liner": "Every Pedigree ad dog is a real shelter dog near you.",
    "creative_mechanisms": [
      "media-as-product",
      "ai-powered-personalization",
      "geolocation-targeting",
      "purpose-driven-product"
    ],
    "qualitative_summary": "Rewires the brand's entire media spend into an adoption engine; each impression doubles as a working ad for a specific, local, adoptable dog."
  },

  "visual": {
    "style_description": "Hero portrait of a single dog on a warm beige background with the Pedigree yellow callout; right side shows a phone mockup of the adoption profile and a small DOOH placement grid.",
    "craft_quality": "high",
    "dominant_colors": ["yellow", "beige", "white", "black"]
  },

  "review_flag": false,
  "review_reasons": []
}
```

**Note**: Pedigree has explicit `context`, `insight`, and `idea` text on the board, so all three `inferred.*` are `null`. `one_liner`, `creative_mechanisms`, and `qualitative_summary` are always required.

---

### Example B — KitKat "Phone Break" (Grand Prix, visual-only, no metrics)

```json
{
  "id": "kitkat-phone-break-vml-prague",
  "tier": "Grand Prix",
  "category": "Outdoor",
  "file_path": "2025/Grand Prix/Outdoor-Grand-Prix-at-Cannes-Lions-2025-KitKat...jpeg",

  "extracted": {
    "campaign": "Phone Break",
    "brand": "KitKat",
    "agencies": [],
    "tagline": "How photography turned a timeless slogan into a timely reminder.",
    "context": null,
    "insight": null,
    "idea": null,
    "execution": [
      "Tram and bus shelter placements in Prague",
      "Public-transport billboards",
      "Hand-to-hand product placement in everyday street moments"
    ],
    "metrics": [],
    "press_coverage": [
      "The Drum",
      "Marketing-Interactive",
      "Ads of Brands"
    ]
  },

  "inferred": {
    "context": "Smartphones have replaced almost every quiet moment in daily life — people no longer 'take breaks' from anything.",
    "insight": "KitKat's 65-year-old 'Have a Break' slogan has new meaning in the smartphone era — a real break now means putting your phone down.",
    "idea": "Photograph everyday street moments where people are about to look at their phones, with a red KitKat in their hand instead — turning the chocolate bar into a phone-free pause.",
    "one_liner": "KitKat replaces the phone in your hand.",
    "creative_mechanisms": [
      "slogan-recontextualisation",
      "everyday-moment-hijack",
      "photography-as-campaign",
      "brand-platform-extension"
    ],
    "qualitative_summary": "Reframes a 65-year-old tagline as a timely commentary on phone addiction; earned industry-wide praise as a craft + brand-consistency benchmark."
  },

  "visual": {
    "style_description": "Bright red KitKat-branded board; one large sun-lit street photograph showing strangers about to look at red-wrapped KitKats; press quotes row above; OOH thumbnail strip below.",
    "craft_quality": "high",
    "dominant_colors": ["red", "white"]
  },

  "review_flag": false,
  "review_reasons": []
}
```

**Note**: KitKat's board carries no written context / insight / idea — all three live in `inferred`. `metrics` is empty (no numbers visible). The impact signal here is carried by the 3+ press outlets, which is enough to finalize.

---

### Example C — UN Women "Child Wedding Cards" (Bronze, qualitative impact only)

```json
{
  "id": "child-wedding-cards-un-women-impact-bbdo-dubai",
  "tier": "Bronze",
  "category": "Direct",
  "file_path": "2025/Bronze/CHILD WEDDING CARDS – UN WOMEN (IMPACT BBDO DUBAI).jpg",

  "extracted": {
    "campaign": "Child Wedding Cards",
    "brand": "UN Women",
    "agencies": [],
    "tagline": "A direct-mail campaign towards lawmakers to increase the minimum age of marriage to 18.",
    "context": "In Pakistan, a significant share of girls are married before 18, some as young as 9 — child marriage is a persistent crisis the legislature has not addressed.",
    "insight": null,
    "idea": "Send members of Pakistan's National Assembly direct-mail wedding invitations hand-drawn by Pakistani girls aged 9 to 18 — confronting lawmakers with the children they are allowing to be married.",
    "execution": [
      "Direct mail wedding-invitation cards hand-drawn by Pakistani girls aged 9-18",
      "Delivered to members of Pakistan's National Assembly",
      "Triggered a National Dialogue / parliamentary debate",
      "Anchored a draft Child Wedding Cards bill"
    ],
    "metrics": [],
    "press_coverage": []
  },

  "inferred": {
    "context": null,
    "insight": "Lawmakers debate child marriage in abstract statistics — but a handwritten wedding invitation from a 9-year-old makes the issue physical, personal, and impossible to file away.",
    "idea": null,
    "one_liner": "Real wedding invitations, drawn by children.",
    "creative_mechanisms": [
      "direct-mail-confrontation",
      "victim-as-author",
      "personalisation-of-statistics",
      "advocacy-through-artefact"
    ],
    "qualitative_summary": "Triggered a National Dialogue in Pakistan's National Assembly and anchored a draft Child Wedding Cards bill — non-quantified but tangible legislative response."
  },

  "visual": {
    "style_description": "Mixed-media advocacy layout: bold hand-written title on a dark backdrop, central hero photo of hands holding a child's wedding-invitation drawing flanked by four more drawings, three short labelled text blocks below.",
    "craft_quality": "medium",
    "dominant_colors": ["black", "blue", "white", "pink"]
  },

  "review_flag": false,
  "review_reasons": []
}
```

**Note**: No metrics, no press coverage on the board — but `inferred.qualitative_summary` captures the legislative outcome (a real, documentable impact). The board is kept in the index thanks to that qualitative impact; without it we would have flagged.

---

## Common traps

1. **Filling `agencies`**. Don't. It's always `[]` because agency names are in the filename, not on the board.
2. **Inferring `context` / `insight` / `idea` in Pass 1**. Forbidden. Pass 1 is literal-only.
3. **`one_liner` over 12 words**. Hard cap. If you can't get under 12, you don't yet understand the idea — re-read the board.
4. **Hex colours in `dominant_colors`**. Use plain English names.
5. **Bare numbers in `metrics`**. "34%" alone is useless — write "34% increase in sales".
6. **English tags with spaces or underscores**. `creative_mechanisms` is kebab-case-only.
7. **No impact evidence anywhere** (no metrics, no press, no qualitative outcome). If you arrive at this state, the board should be **flagged** instead of extracted.

---

