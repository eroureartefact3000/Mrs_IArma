# Rules

> The 12 non-negotiable rules every subagent follows. Self-contained, no references to other files.

---

## 1. Rules are the source of truth

If your task brief and a rule below disagree, the rule wins.

If a rule is ambiguous, **stop and report** in your task summary. Do not guess and do not improvise.

---

## 2. Strict no-invention on Pass 1

For Pass 1 extraction (the literal pass), a field's value reflects what is **literally readable on the board** — not what you guess or infer.

### How to handle text that's small or dense

Boards often pack 2-4 paragraphs of small body text into side columns. **Read them carefully — do not skip them just because they're small.** Most boards are designed for a jury panel that zooms in, so the body text IS meant to be read.

Apply this **confidence ladder** field by field:

| You can confidently read … | Action |
|---|---|
| ≥ 80% of the field's text | Transcribe it. Paraphrase tightly to English. |
| 50–80% — most words clear, a few illegible | Transcribe what you can. Mark unreadable spans with `[…]`. Keep the field non-null. |
| < 50% — paragraph mostly unreadable | Use `null`. |
| Field genuinely absent from the board | Use `null`. |

The point: a partially-readable paragraph carries far more signal than `null`. Don't drop a whole paragraph over a few illegible words.

### What's still forbidden

- Inferring values from context absent from the board ("I'm sure they meant…")
- Paraphrasing a missing field from a related one ("the agency must be X since…")
- Filling in defaults to look helpful
- Guessing words to make the transcription read smoothly

### What `null` still means

- The board genuinely doesn't have that section, OR
- You can read less than 50% of the field's content with confidence

`null` is a legitimate value — use it when warranted, but **not** as a shortcut to skip difficult-but-readable text. Inference (filling missing fields from context + visuals) is the job of Pass 2.

---

## 3. Validate before write

Before writing any JSON file:

1. Confirm every required field is present (even if `null`)
2. Confirm types match the schema (string where string, list where list, etc.)
3. Confirm enum values are inside the allowed set (e.g. `craft_quality ∈ {"high","medium","low"}`)
4. Confirm no extra fields outside the schema

If anything is uncertain, **do not write**. Add the board to flagged output instead.

---

## 4. Never overwrite an existing output file

Before writing `extractions/<cat>/<slug>.json` (or any other output file), check whether it already exists.

- If it exists → **skip the board** and log `already_done: <slug>` in your task summary
- If it does not exist → write it

This makes runs resumable: if a session crashes, re-running the same brief picks up where it stopped.

---

## 5. No files outside the output path defined for your task

The only files you create are the output files specified in your task brief for your role. No:

- Temp files
- Log files
- Cache files
- Debug dumps
- Markdown notes
- Backup copies

If you need to remember something while working, keep it in your context. Persistence is the orchestrator's job, not yours.

---

## 6. Report errors and continue; stop only on repeated identical errors

If a JSON you produce fails validation (rule 3), **flag that board** (rule 12 reason `extraction_failed`), record the failure in your task summary, and **continue to the next board**. One bad board does not poison the rest of the batch.

For each failure, your task summary must record:

- The board file path
- The field that failed
- The specific reason (e.g. "string expected, got list")

**Hard stop condition** — stop the batch entirely when the **same type of error on the same type of field** happens **3 times in a row**. That pattern signals a systemic issue (broken schema, ambiguous brief, source-data drift) — keep going would just pile up bad records. When you stop, report the 3 occurrences in your summary and let the orchestrator decide.

"Same type of error" means: same failing field name AND same failure mode (e.g. three boards in a row where `one_liner` ended up over 12 words → stop; one board over 12 words, one missing `metrics`, one with the wrong `craft_quality` enum → keep going, those are different problems).

---

## 7. No communication between subagents

You work alone on your batch. You do not:

- Read other subagents' outputs to "harmonise" with them
- Try to coordinate timing or content with peers
- Inspect files outside your scope (other categories, calibration data, etc.)

The orchestrator coordinates. You execute.

---

## 8. Language: English everywhere

The product is English-language. Your output is **always in English**, regardless of the source material's language (boards may have French, Portuguese, Mandarin etc. text on them — your output is still English).

Exceptions:
- **Quotes** from the board may be preserved in their original language inside a string field, but the field itself is described in English (e.g. `"press_quotes": ["Excellent travail — Le Monde"]` is fine).
- **Technical tags** in `creative_mechanisms` are always English kebab-case (e.g. `everyday-object-transformation`).

Mystic / poetic phrasing is **not** your job. Stay neutral, factual, technical.

---

## 9. No tone — be neutral

You are a technical extractor / analyst. Your output reads like a database record or a jury reviewer's structured notes, not like marketing copy.

Avoid:
- Superlatives ("brilliant", "exceptional") unless they are themselves a documented field in the schema (the `judge` role may use them when justified)
- Emojis
- Rhetorical flourishes
- Speculation about what the agency "really meant"

---

## 10. Tags in `creative_mechanisms` follow the kebab-case convention

When you generate `creative_mechanisms` (Pass 2):

- Always English
- Always lowercase
- Words joined by hyphens (kebab-case)
- 2-5 words per tag, ideally 3
- 3-5 tags per board, never more

Good examples:
- `everyday-object-transformation`
- `celebrity-as-prop`
- `platform-jailbreak`
- `cultural-symbol-subversion`
- `purpose-driven-product`

Bad examples:
- `Everyday Object Transformation` ← wrong case
- `everyday_object_transformation` ← wrong separator
- `transformation` ← too vague
- `the-mechanism-of-turning-everyday-objects-into-advertising-media` ← too long

---

## 11. Report board-level issues; never hide them

If something looks wrong about a board (corrupted image, off-topic content, suspicious metadata, etc.), **flag it** (rule 12) — do not silently produce a degraded record.

Better to flag 10 boards for human review than to silently emit 10 weak records that pollute the index.

---

## 12. Flag unreadable boards

If you cannot reliably extract a board, write a **flag file** instead of an extraction file.

Triggers for flagging:

| Trigger | When |
|---|---|
| `corrupted` | `Read` tool fails or returns an unreadable image |
| `low_resolution` | Image is so small that text on the board is illegible (e.g. < 600 px wide, blurry, key numbers unreadable) |
| `off_topic` | The image is clearly not a Cannes Lions board (e.g. a stock photo, a logo only, a screenshot of an interface) |
| `wrong_category` | The board is clearly NOT in the category your task targets (e.g. an obvious Film board in the PR batch) |
| `extraction_failed` | You can read the image but cannot fill 2+ essential fields (e.g. neither `campaign` nor `brand` is determinable, even with reasonable effort) |

**Flag file format**:

```json
{
  "file_path": "<original board path>",
  "slug": "<canonical slug>",
  "category": "<category>",
  "reason": "corrupted | low_resolution | off_topic | wrong_category | extraction_failed",
  "detail": "<one short sentence describing what you saw>",
  "subagent_role": "extraction_pass1 | extraction_pass2 | rationale"
}
```

When you flag a board, **do not** also write an extraction file for it. Skip to the next board.
