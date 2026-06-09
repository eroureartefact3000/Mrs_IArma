# Output locations

> Where to write what. Strict paths and slug rules. Self-contained, no references to other files.

---

## The 3 output buckets

There are **only three** places a subagent ever writes:

```
data_internal/
├── extractions/<category>/<slug>.json    ← Pass 1 + Pass 2 combined output
├── rationales/<category>/<slug>.json     ← why-it-won output (winners only)
└── flagged/<category>/<slug>.json        ← unreadable boards (rule 12)
```

- `<category>` is the **lowercased Cannes Lions category** with non-alphanumerics replaced by hyphens. See the slug rules below — same logic applied to the category name. Examples:
  - `Outdoor` → `outdoor`
  - `PR` → `pr`
  - `Health & Wellness` → `health-wellness`
  - `Entertainment for Gaming` → `entertainment-for-gaming`
- `<slug>` is the canonical board id (see slug rules below).

---

## Slug rules — how to build `<slug>` from a board filename

Take the board file's **stem** (filename without extension) and normalise it:

1. Lowercase everything
2. Replace each of these characters with a single hyphen: space, `–` (en-dash), `(`, `)`, `/`, `_`, `,`, `.`
3. Collapse multiple consecutive hyphens into one
4. Strip leading/trailing hyphens
5. Truncate to a maximum of **80 characters**

Example:

```
Filename: "Adoptable - Pedigree (Colenso BBDO, Auckland).webp"
Stem:     "Adoptable - Pedigree (Colenso BBDO, Auckland)"
Step 1:   "adoptable - pedigree (colenso bbdo, auckland)"
Step 2:   "adoptable---pedigree--colenso-bbdo--auckland-"
Step 3:   "adoptable-pedigree-colenso-bbdo-auckland-"
Step 4:   "adoptable-pedigree-colenso-bbdo-auckland"
Step 5:   (already < 80 chars)
SLUG:     "adoptable-pedigree-colenso-bbdo-auckland"
```

If your task brief gives you the slug for each board, **use the slug from the brief verbatim**. Do not recompute. The brief's slug is the source of truth.

If your task brief gives only filenames, apply the rules above and produce slugs yourself.

---

## File naming inside each bucket

For a board with `slug = "adoptable-pedigree-colenso-bbdo-auckland"` in category Outdoor:

| Role | Output file path |
|---|---|
| Pass 1 + Pass 2 (combined) | `data_internal/extractions/outdoor/adoptable-pedigree-colenso-bbdo-auckland.json` |
| Rationale (winners only) | `data_internal/rationales/outdoor/adoptable-pedigree-colenso-bbdo-auckland.json` |
| Flagged (unreadable) | `data_internal/flagged/outdoor/adoptable-pedigree-colenso-bbdo-auckland.json` |

**One board produces exactly one file in exactly one bucket.** Never write the same slug to two buckets — flagged or extracted, never both.

---

## What goes in each output bucket

### `extractions/<cat>/<slug>.json`

The full Pass 1 + Pass 2 record (with the `visual` block). Used downstream as the input to:
- The judge (when this board is later submitted as a candidate)
- Rationale generation (when this is a known winner)

### `rationales/<cat>/<slug>.json`

The "why this board won its tier" record. Built only for winners that already have a known tier (Grand Prix / Gold / Silver / Bronze / Shortlist / Loser). Used as input to the RAG index.

### `flagged/<cat>/<slug>.json`

Boards the subagent could not reliably handle. Reviewed manually later by a human.

---

## Directory creation

Your `Write` tool call will create missing directories automatically when needed. You do **not** need to use any other mechanism to create folders.

If for some reason `Write` fails because of a missing directory, report the failure with the full path you tried — the orchestrator will fix it.

---

## What you do NOT write

For clarity, the following paths are **off-limits** for any subagent:

- `pipeline/` and any subfolder — that's the source code, never touch
- `api/`, `mini_frontend/`, `scripts/`, `tests/` — same
- `data/` — production assets (RAG index files), curated by the orchestrator, **read-only** for subagents
- `2024/`, `2025/`, `loser/` — source datasets, **read-only**
- `agent_briefs/` itself — these briefs are the contract, you don't edit them
- `.env`, `.gitignore`, root config files

If your task accidentally pushes you toward writing to one of these paths, **stop and report**.
