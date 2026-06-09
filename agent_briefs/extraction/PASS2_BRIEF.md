# Pass 2 brief — Inference + visual

> Procedure for Pass 2 of extraction: (1) fill gaps left by Pass 1 via careful inference, (2) describe the board's visual style, (3) produce the mandatory `one_liner`, `creative_mechanisms`, and `qualitative_summary`. Self-contained, no references to other files.

---

## What Pass 2 does

For each board in your batch:

1. **Read** the existing Pass 1 partial record at `data_internal/extractions/<category>/<slug>.json`
2. **Read** the board image again with the `Read` tool
3. Build the `inferred` block:
   - For each of `context`, `insight`, `idea`: if `extracted.<field>` is `null`, infer from the board + filled `extracted` fields. If you're not confident, leave the inferred value `null`. If `extracted.<field>` is already filled, set the corresponding `inferred.<field>` to `null` (we only infer what was missing).
   - `one_liner`: always required, ≤ 12 words, punchy
   - `creative_mechanisms`: 3-5 kebab-case English tags
   - `qualitative_summary`: 1-2 sentences capturing the impact narrative
4. Build the `visual` block (always required):
   - `style_description`: 1-2 sentences
   - `craft_quality`: high | medium | low
   - `dominant_colors`: 2-4 plain English colour names
5. Verify the board still has at least some impact evidence (`metrics` non-empty OR `press_coverage` non-empty OR a meaningful `qualitative_summary`). If none of these is true, do **not** finalize this record — write a flag file instead.
6. **Overwrite** the file at `data_internal/extractions/<category>/<slug>.json` with the complete record.

> **Important**: Pass 2 is the only time rule 4 ("no overwrite") is relaxed — and only for upgrading a Pass 1 partial record (where `visual` is `null` and `inferred.one_liner` is `null`) into a complete one. If you read a file and `visual` is already non-null, that means Pass 2 was already done — skip the board and log `already_done`.

---

## How to decide between filling and leaving `null` in `inferred.{context,insight,idea}`

You should fill an inferred field **only when**:

- The board's visuals + tagline + execution strongly imply it
- You can defend the inference in one sentence ("the strapline says 'Have a Break' and the visuals show a phone replaced by a chocolate bar → the insight is clearly 'phones killed real breaks'")
- A reasonable second jury would arrive at the same inference

You should leave it `null` when:

- You'd be inventing rather than reading between the lines
- Two equally plausible inferences exist and the board doesn't disambiguate
- You catch yourself starting with "they probably meant…" — that's a sign to leave `null`

When in doubt, **leave `null`**. An empty `inferred.idea` is fine; a wrong one is harmful.

---

## How to write a strong `one_liner`

The `one_liner` is the single most important piece of text the system uses downstream (it's the RAG search anchor and the headline shown to users). Get it right.

### Hard requirements

- **≤ 12 words** (count them)
- No gerunds at the start ("Turning", "Making", "Letting")
- No metric numbers
- English only
- One sentence, ending in a period

### Style patterns to imitate

```
"The train ticket IS the lottery ticket."
"The pill becomes the helpline."
"Every Pedigree ad dog is a real shelter dog."
"Real wedding invitations, drawn by children."
"KitKat replaces the phone in your hand."
"The sponsorship IS the absence of sponsorship."
"The sidewalk becomes the map."
```

Notice the patterns:
- `"X IS Y"` (declaration of equivalence)
- `"X becomes Y"` (transformation)
- `"<noun phrase>"` (compressed metaphor)

### Write multiple candidates, pick one

Generate 3 candidates in your head before picking. The winning one is usually:
- The shortest
- The one that loses no meaning if read with no other context

---

## How to write `creative_mechanisms`

3-5 tags. Each describes the **creative move**, not the topic.

| ✓ Good | ✗ Bad | Why |
|---|---|---|
| `everyday-object-transformation` | `train-tickets` | Tag describes the move, not the topic |
| `algorithm-hijack` | `fifa-game` | Mechanism, not subject matter |
| `slogan-recontextualisation` | `kitkat-ad` | Mechanism, not brand |
| `media-as-product` | `outdoor-advertising` | Mechanism, not channel |

Stay in the kebab-case-only convention.

Common good tags (non-exhaustive): `everyday-object-transformation`, `celebrity-as-prop`, `ambient-media-hijack`, `platform-jailbreak`, `data-as-content`, `ritual-creation`, `cultural-symbol-subversion`, `purpose-driven-product`, `algorithm-hijack`, `name-as-content`, `rights-circumvention`, `slogan-recontextualisation`, `direct-mail-confrontation`, `legislative-advocacy`, `media-as-product`. Invent new ones when none of the above fits.

---

## How to write `qualitative_summary`

A 1-2 sentence narrative summary of impact. It captures the **outcome story** — cultural footprint, behavioural change, business shift — in a form a juror would write in their notes.

### Tone

Descriptive, not promotional. No superlatives.

| ✓ Good | ✗ Bad |
|---|---|
| "Rewires brand media spend into an adoption engine; each impression doubles as a working ad for a specific, local, adoptable dog." | "An exceptional, world-first innovation that revolutionised pet adoption forever." |
| "Triggered a National Dialogue in Pakistan's National Assembly and anchored a draft Child Wedding Cards bill — non-quantified but tangible legislative response." | "Made huge waves in Pakistan and pushed the government to do the right thing." |

### When the board has metrics

Reference the largest 1-2 metrics inside the summary, calibrated to scale:
> *"$685M revenue lift and 95% positive sentiment on a national rail behavioural-change campaign."*

### When the board has no metrics

Capture the qualitative outcome (cultural pickup, legislative shift, partner reaction, etc.). If there is **no** documentable outcome on the board, you should be flagging — but if you choose to finalize the record, this field captures whatever impact narrative the board does carry.

---

## How to describe `visual`

### `style_description`

1-2 sentences describing the board's composition. **The first thing to capture is the hero visual — the specific scene or motif that carries the creative concept**. Then add layout / craft notes.

A good `style_description` answers, in order:

1. **What is the hero visual literally showing?** Be specific about the subjects, their action, and the framing. Examples:
   - *"Two women — a mother and her daughter — filmed in mirrored close-ups, each at the wheel of one of two Volkswagen Kombis (vintage and modern), on the same desert road."*
   - *"A warm portrait of a Honduran Sky Fisher in a cowboy hat holding the Heaven Fish pack."*
   - *"A glowing red KitKat bar swapped in for a smartphone in a candid street photograph."*

2. **How is the rest of the board composed around it?** Layout, density, supporting elements:
   - Layout type (editorial / poster / collage / grid / hero-shot dominant)
   - Photo vs illustration vs CGI vs mixed
   - Density (sparse / balanced / dense)
   - Tone (bright / dark / cinematic / clinical / playful)
   - Distinctive visual devices (typography choice, signature colour, recurring motif)

**Bad examples** (generic, miss the concept):
- *"Cinematic film-still hero with metric block column and dense press strip."*  ← describes layout but not what the hero shows
- *"Editorial board with photography and text columns."*  ← could be any board
- *"Polished and clean."*  ← says nothing

**Good examples** (concept-first):
- *"Two women in vintage and modern VW Kombis on the same road, filmed as mirrored close-ups that make the duet's intergenerational concept literal; metrics tower on the right; dense press logo strip at the bottom."*
- *"Hand-drawn fish-under-a-halo logo as the hero, set against a clean off-white background; left half is a dense brand-identity system, right half is a warm Sky Fisher portrait, bottom strip shows merch and packaging shots."*

### `craft_quality`

Three labels — be honest. Most Cannes Lions winning boards are `"high"`; some Bronze and Shortlist boards are `"medium"`; losers are often `"low"`.

| Label | Look |
|---|---|
| `high` | Polished, intentional typography, considered composition, professional photography or CGI, no eyesores |
| `medium` | Clean and professional but unremarkable. Nothing wrong, nothing exceptional. |
| `low` | Visible amateur tells: clashing typefaces, misaligned grids, low-resolution stock photos, awkward composition |

### `dominant_colors`

2-4 colours. Plain English. The actual colour the eye picks up on the board, not the brand's marketing palette.

Examples:
- `["red", "white"]` (KitKat)
- `["yellow", "beige", "black"]` (Pedigree)
- `["black", "blue", "pink"]` (UN Women)

Avoid: hex codes, "Pantone 185 C", "warm tones".

---

## Final impact check before finalizing

Before overwriting the record, verify the board carries at least some impact signal:
- `extracted.metrics` is non-empty, OR
- `extracted.press_coverage` is non-empty, OR
- `inferred.qualitative_summary` is a meaningful 1-2 sentence outcome narrative

If **none** of these is true, do **not** finalize this record. Move it to a flag file at `data_internal/flagged/<cat>/<slug>.json` with `reason: "extraction_failed"` and `detail: "No impact evidence detected after Pass 2."`. Delete the partial Pass 1 file at `data_internal/extractions/<cat>/<slug>.json` so it doesn't poison the index.

---

## Reporting your batch

When you finish, return a short summary:

```
PASS 2 SUMMARY
==============
Boards processed: 24
  ✓ finalized:   22
  ⚑ flagged:     1 ([slug])
  ↻ skipped:     1 ([slug] already finalized)
  ✗ errors:      0

If errors > 0, list them:
  - [slug] field: <field> reason: <reason>
```

Do not write this summary to disk. Return it in your final message.
