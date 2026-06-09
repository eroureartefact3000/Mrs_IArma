# Pass 1 brief — Literal extraction

> Procedure for Pass 1 of extraction: extract what is literally visible on the board into the `extracted` block of the schema. No inference. Self-contained, no references to other files.

---

## What Pass 1 does

For each board in your batch:

1. Read the board image with the `Read` tool
2. Decide whether the board is readable (else flag it)
3. Build the `extracted` block of the schema by extracting **only literally-visible** information
4. Write the **partial record** to `data_internal/extractions/<category>/<slug>.json`

A Pass 1 partial record has:
- `id`, `tier`, `category`, `file_path` (from task brief)
- `extracted` filled (strict literal-only — never invent)
- `inferred` is `null` for every field (Pass 2 fills it later)
- `visual` is `null` (Pass 2 fills it)
- `review_flag: false`, `review_reasons: []` unless your task brief tells you otherwise

The orchestrator (or a Pass 2 subagent) will later merge in the `inferred` and `visual` blocks.

---

## The Pass 1 partial record shape

Use this exact template:

```json
{
  "id": "<slug from task brief>",
  "tier": "<tier from task brief>",
  "category": "<category from task brief>",
  "file_path": "<file_path from task brief>",
  "extracted": {
    "campaign": null,
    "brand": null,
    "agencies": [],
    "tagline": null,
    "context": null,
    "insight": null,
    "idea": null,
    "execution": [],
    "metrics": [],
    "press_coverage": []
  },
  "inferred": {
    "context": null,
    "insight": null,
    "idea": null,
    "one_liner": null,
    "creative_mechanisms": [],
    "qualitative_summary": null
  },
  "visual": null,
  "review_flag": false,
  "review_reasons": []
}
```

Start from this template, then fill the `extracted` block from what you literally see on the board.

---

## Pass 1 mental checklist

Run through the board top-to-bottom (boards are typically organised: header → context → insight → idea → execution → metrics → press at the bottom). For each field, ask the same question:

> *"Is this written explicitly somewhere on the board?"*

| Answer | Action |
|---|---|
| Yes, in plain text | Paraphrase tightly, keep meaning intact, English-only. Fill the field. |
| Yes, but only in another language | Translate tightly to English. Fill the field. |
| Yes, but only encoded in a chart / number / icon | Treat as Pass 2 material — leave `null` in Pass 1. **Exception**: `metrics` can include a chart's numeric value if the unit is unambiguous (e.g. "34%" with an "increase in sales" label). |
| No, only implied | `null`. (Pass 2 may infer it.) |
| Almost-yes, but you'd be paraphrasing from absent text | `null`. |

For lists (`execution`, `metrics`, `press_coverage`):
- Empty list `[]` means "I saw nothing of this kind on the board"
- A non-empty list means "I saw at least one literal item"

---

## Field-by-field guidance

### `campaign`
The campaign's name as printed. Usually the biggest text on the board, often near the top. If the board shows only a brand logo and no campaign name → `null` (Pass 2 may infer from filename, but you do not).

### `brand`
The brand / advertiser. Read the logo. If the logo is purely visual and the brand isn't spelled out → `null`.

### `agencies`
**Always `[]`**. Agency credits are in filenames, not on boards.

### `tagline`
The headline phrase under the title — the campaign's strapline. Not the campaign name itself.

### `context`
The "PROBLEM" / "BACKGROUND" / "CHALLENGE" paragraph. Paraphrase to max ~300 chars. If the board jumps straight to the idea with no problem statement → `null`.

### `insight`
The "INSIGHT" paragraph — the consumer / cultural truth that motivates the idea. If absent → `null`.

### `idea`
The "IDEA" paragraph in 1-2 sentences. This is the core of the campaign. If the board only shows execution shots with no written idea statement → `null` (Pass 2 will infer).

### `execution`
List of channels / mechanics / activations.
- Include items from clearly-labelled "EXECUTION" / "ROLLOUT" text blocks
- Include items shown in an **unambiguous visual strip** at the bottom (OOH photos, app screens, gameplay shots, on-site installations)
- Each item is one short bullet
- 2-7 items typical

### `metrics`
Quantified results. **Always unit + number**.
- "34% increase in sales" ✓
- "$685M revenue" ✓
- "560M impressions" ✓
- "560M" alone ✗ (no unit)
- "millions of views" ✗ (no number)
- If the unit is unreadable, skip the item

### `press_coverage`
- Outlet names (BBC, AdAge, Fast Company, etc.) typically shown as logos
- Or short journalist quotes ("Brilliantly subversive — Campaign")

---

## Decision: extraction or flag?

Before writing your record, ask:
- Does `extracted` have at least `campaign` OR `brand`? (At least one essential field filled.)
- AND does the board show any impact evidence at all — at least one item in `metrics`, in `press_coverage`, or visible enough to be summarised later?

If either answer is no, **flag** the board instead — write to `data_internal/flagged/<category>/<slug>.json`. Do not write a partial extraction.

---

## Reporting your batch

When you finish your batch, return a short summary in this shape:

```
PASS 1 SUMMARY
==============
Boards processed: 24
  ✓ written:     21
  ⚑ flagged:     2 ([slug1] [slug2])
  ↻ skipped:     1 ([slug3] already existed)
  ✗ errors:      0

If errors > 0, list them:
  - [slug] field: <field> reason: <reason>
```

Do not write this summary to disk. Return it in your final message.
