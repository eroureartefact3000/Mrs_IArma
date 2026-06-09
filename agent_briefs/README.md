# `agent_briefs/` — source of truth for Mrs IArma subagents

> These markdown files **are the contract** between the orchestrator and subagents. The orchestrator's task brief specifies which files a given subagent reads. Editing one file here changes behaviour for every future run.

---

## Why this directory exists

- A **single, versioned source of truth** for every rule a subagent must follow
- **Edit once, applies everywhere** — change a rule by editing the relevant file, no need to touch orchestrator code or prompts
- **MECE** — each file owns its topic exclusively, no cross-references between files

---

## File index (what each file owns)

| File | Owns |
|---|---|
| `00_MISSION.md` | Project context: what Mrs IArma is, the pipeline shape, the 4 judging axes, the tools subagents have access to |
| `01_RULES.md` | The 12 non-negotiable rules for any subagent |
| `02_OUTPUT_LOCATIONS.md` | Exact output paths, slug convention, write boundaries |
| `extraction/SCHEMA_REFERENCE.md` | The v3 extraction JSON schema, field-by-field, with 3 worked examples |
| `extraction/PASS1_BRIEF.md` | Procedure for the literal extraction pass |
| `extraction/PASS2_BRIEF.md` | Procedure for the inference + visual pass |
| `rationale/DA_PATTERNS.md` | Strategy=WHY, Execution=HOW mental model + 5 RIGOUR patterns |
| `rationale/RATIONALE_BRIEF.md` | Procedure for generating "why-it-won" rationales |
| `categories/OUTDOOR.md` | Outdoor category specifics: axis weights, sub-categories, native-to-category check |
| `categories/<other>.md` | Same shape per category, created as new categories are onboarded |

---

## How a subagent gets its briefing

The **orchestrator's task brief** (passed at spawn time) tells the subagent:

1. Which files in this directory to read, in what order
2. The specific batch of boards/extractions to process
3. Any temporary parameters not in the contract (e.g. retry policies)

The subagent reads only the files listed in its task brief. It does not browse this directory on its own.

---

## How to add a new category

1. Copy `categories/OUTDOOR.md` to `categories/<NEW>.md`
2. Adjust axis weights to reflect the category's official Cannes Lions judging emphasis
3. Adjust the sub-categories list to match the entry kit
4. Adjust the "native-to-category check" patterns (every category has its own signature offenders)
5. Update the patterns commonly seen in winners
6. Register the category in the orchestrator code (`pipeline/__init__.py` registry)

Universal rules (DA model, RIGOUR, output locations) live in their own files and stay unchanged.
