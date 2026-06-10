"""LLM-Judge v3.1 — pairwise reasoning + structured tool output.

Major rewrites:
  - v3 (2026-05-29): pairwise comparison + tier probabilities (D2+C6).
  - v3.1 (2026-05-29): use Anthropic's `tools` API to force JSON schema —
    eliminates JSON parse failures (2/10 cases in v3 had malformed output).
    Pairwise comparison stays in the prompt as a reasoning GUIDE; we only
    capture the structured judgement (axes + probs + verdict).
"""
from __future__ import annotations

import json
import statistics
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .category_registry import require_enabled_category
from .client import MODEL, build_media_block, get_client
from .images import load_image_for_api
from .schema import AxisScore, Extracted, Inferred, Reference, Visual

_TIERS = ("Grand Prix", "Gold", "Silver", "Bronze", "No Medal")


# Tool schema forcing the LLM to output valid structured judgement.
_JUDGEMENT_TOOL = {
    "name": "submit_judgement",
    "description": (
        "Submit your structured evaluation of the candidate board. "
        "Provide per-axis scores with rationale, a probability distribution over the 5 outcome tiers, "
        "a 1-2 sentence verdict, and concrete strengths/weaknesses."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "axis_scores": {
                "type": "object",
                "description": "Per-axis score 0-100 with 2-3 sentence rationale citing board-visible evidence.",
                "properties": {
                    axis: {
                        "type": "object",
                        "properties": {
                            "score": {"type": "integer", "minimum": 0, "maximum": 100},
                            "rationale": {"type": "string", "description": "2-3 sentences with concrete observations"},
                        },
                        "required": ["score", "rationale"],
                    }
                    for axis in ("idea", "strategy", "execution", "impact")
                },
                "required": ["idea", "strategy", "execution", "impact"],
            },
            "tier_probabilities": {
                "type": "object",
                "description": "Probability distribution over the 5 outcome tiers. Must sum to 1.0.",
                "properties": {
                    tier: {"type": "number", "minimum": 0, "maximum": 1}
                    for tier in _TIERS
                },
                "required": list(_TIERS),
            },
            "verdict": {
                "type": "string",
                "description": "1-2 sentences naming THE deciding factor for the prediction.",
            },
            "key_strengths": {
                "type": "array",
                "items": {"type": "string"},
                "maxItems": 5,
                "description": "2-4 concrete strengths citing board-visible elements.",
            },
            "key_weaknesses": {
                "type": "array",
                "items": {"type": "string"},
                "maxItems": 5,
                "description": "2-4 concrete weaknesses citing board-visible elements.",
            },
            "synthesis": {
                "type": "string",
                "description": (
                    "WRITE IN ENGLISH. 1-2 short diagnostic sentences (max ~40 words total) EXPLAINING the prediction "
                    "as a post-mortem observation, since boards have already been submitted to the jury. "
                    "DO NOT suggest fixes or improvements. "
                    "The tone is that of a jury post-deliberation note: what the board does well "
                    "and what limits it, framed as observation, not advice. "
                    "Example: 'Memorable idea and clean execution, but the impact proof is too thin: "
                    "the cited percentages are not anchored to absolute bases, which caps the jury read.' "
                    "AVOID imperative verbs like 'Add', 'Strengthen', 'Specify'. Use descriptive language instead. "
                    "FORBIDDEN PUNCTUATION: do not use em dashes (—) or en dashes (–). "
                    "Use commas, semicolons, colons, or periods instead. "
                    "FORBIDDEN STYLISTIC TICS: avoid 'It's not just X, it's Y' constructions and similar AI-sounding patterns."
                ),
            },
        },
        "required": [
            "axis_scores", "tier_probabilities", "verdict",
            "key_strengths", "key_weaknesses",
            "synthesis",
        ],
    },
}


_JUDGE_PROMPT = """You are a Cannes Lions {category} jury member evaluating a NEW entry.
You don't know the outcome — your task is to estimate it via PAIRWISE COMPARISON against 7 reference past entries (5 winners + 2 non-winners), then express your prediction as a probability distribution over tiers.

== THE NEW BOARD ==
The image is attached above. Here is its structured extraction:

{extraction_json}

== 7 REFERENCE PAST ENTRIES (RAG retrieval) ==
These are 7 of the most similar past Outdoor entries from the 2024 jury:
  - **5 WINNERS** (Grand Prix / Gold / Silver / Bronze) — calibrate the upper bound: how good must the candidate be to medal?
  - **2 NON-WINNERS** (Shortlist / Loser) — calibrate the lower bound: what does work that DIDN'T medal look like?
Use BOTH sets. If the candidate is closer in quality to the non-winners than to the winners, give significant weight to "No Medal" in your probability distribution.

{references_block}

== JUDGING CRITERIA ({category}) ==
{criteria_json}

== HARD RULES ==

STRATEGY axis = WHY (and ONLY why). Answer in order:
  1. WHO IS THE BRAND? Identify the brand and its mission (especially if not internationally known).
  2. Is the idea coherent with that brand's mission?
  3. Are the context and insights real, verifiable, data-backed? Cite specific data points.
Do NOT discuss orchestration, media choices, channels, or amplification under Strategy.

EXECUTION axis = HOW (and ONLY how). Answer:
  - Are the means and media chosen relevant to the objective and the target?
  - Phases of the campaign? Channels? Amplification layers?
Do NOT discuss brand mission, insight quality, or context veracity under Execution.

RIGOUR & SKEPTICISM (agencies stage their results):
  1. PERCENTAGES WITHOUT BASE → "X% of what?" If base missing, treat as soft claim.
  2. UNVERIFIED PRESS / NUMBERS → claims, not facts. Flag load-bearing claims.
  3. MISSING REAL BUSINESS OUTCOME → identify the brand's likely objective; surrogates (impressions, reach) are weaker.
  4. NO VAGUE SUPERLATIVES → justify immediately or drop.
  5. CULTURAL / LINGUISTIC PRECISION → identify the scope (Québec-only ≠ pan-Canadian).

NATIVE-TO-CATEGORY CHECK:
If the work is essentially a different category dressed as {category} (live event re-shot as OOH, Twitch stunt called outdoor, etc.), reflect this in your scoring AND in the probability distribution (push significant weight to "No Medal").

== REASONING METHOD — PAIRWISE COMPARISON (use this to think, you don't need to output the comparisons) ==

For each axis, mentally compare the candidate against each of the 7 references (both winners AND non-winners):
  • Is the candidate stronger / similar / weaker than this reference on this axis? By how many points?
  • Calibration: much_stronger = +10 to +20, stronger = +3 to +10, similar = -2 to +2, weaker = -3 to -10, much_weaker = -10 to -20.
  • The candidate's score for an axis ≈ average of (reference_score + your_pairwise_delta) across all 7 references, weighted toward the most similar ones.
  • IMPORTANT: if the candidate is most similar to the non-winners (Shortlist/Loser), that's a strong signal it won't medal — reflect this in your probabilities.

Then aggregate into per-axis scores and a tier probability distribution.

== TIER PROBABILITY DISTRIBUTION GUIDANCE ==

  - Probabilities must sum to 1.0.
  - If candidate is bracketed clearly between two reference tiers, distribute weight between them.
  - If candidate clearly outperforms all GP references → weight Grand Prix high.
  - If candidate clearly underperforms even the lowest medal reference, or fails the native-to-category check → give significant weight to "No Medal".
  - Honest uncertainty: "Silver leaning Gold" = e.g. {{Silver: 0.45, Gold: 0.30, Bronze: 0.15, GP: 0.05, No Medal: 0.05}}. Don't concentrate all weight on one tier unless you're very confident.

== OUTPUT ==

Call the `submit_judgement` tool with your structured evaluation. Do not output free text — only the tool call."""


def _format_references_block(references: list[Reference]) -> str:
    blocks = []
    for i, r in enumerate(references, start=1):
        block = (
            f"--- REF{i} (id: {r.id}) ---\n"
            f"  tier: {r.tier}  ·  weighted_score: {r.weighted_score}\n"
            f"  campaign: {r.campaign or '?'}  ·  brand: {r.brand or '?'}\n"
            f"  one_liner: {r.one_liner or ''}\n"
            f"  verdict: {r.verdict or ''}\n"
            f"  similarity_to_new_board: {r.similarity_score:.3f}\n"
        )
        blocks.append(block)
    return "\n".join(blocks)


def _normalise_probs(raw: dict[str, float]) -> dict[str, float]:
    out = {t: max(0.0, float(raw.get(t, 0.0))) for t in _TIERS}
    total = sum(out.values())
    if total <= 0:
        return {t: 1.0 / len(_TIERS) for t in _TIERS}
    return {t: v / total for t, v in out.items()}


_MAX_RETRIES = 2


def _judge_single(
    image_b64: str,
    media_type: str,
    extraction_json: str,
    references_block: str,
    criteria_json: str,
    category: str,
) -> dict[str, Any]:
    prompt = _JUDGE_PROMPT.format(
        category=category,
        extraction_json=extraction_json,
        references_block=references_block,
        criteria_json=criteria_json,
    )
    client = get_client()
    last_err: Exception | None = None
    for _ in range(_MAX_RETRIES + 1):
        try:
            msg = client.messages.create(
                model=MODEL,
                max_tokens=3000,
                tools=[_JUDGEMENT_TOOL],
                tool_choice={"type": "tool", "name": "submit_judgement"},
                messages=[
                    {
                        "role": "user",
                        "content": [
                            build_media_block(image_b64, media_type),
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
            )
            # Extract the tool_use block
            tool_use_blocks = [b for b in msg.content if getattr(b, "type", None) == "tool_use"]
            if not tool_use_blocks:
                last_err = RuntimeError("Model did not call submit_judgement tool")
                continue
            data = dict(tool_use_blocks[0].input)
            # Validate axis_scores
            for axis in ("idea", "strategy", "execution", "impact"):
                AxisScore(**data["axis_scores"][axis])
            data["tier_probabilities"] = _normalise_probs(data["tier_probabilities"])
            return data
        except (ValidationError, KeyError, TypeError, json.JSONDecodeError) as e:
            last_err = e
    raise last_err  # type: ignore[misc]


def judge_board(
    image_path: Path,
    extracted: Extracted,
    inferred: Inferred,
    visual: Visual,
    references: list[Reference],
    n_passes: int = 3,
    criteria: dict[str, Any] | None = None,
    category: str = "Outdoor",
) -> dict[str, Any]:
    """Multi-pass judge with tool-enforced JSON schema. Returns averaged axis
    scores + averaged tier probability distribution + narrative from the
    centroid pass.

    `criteria` may be passed explicitly (test seam). If omitted, the criteria
    for `category` are loaded from the registry.
    """
    if criteria is None:
        criteria = require_enabled_category(category).criteria
        assert criteria is not None

    b64, media_type = load_image_for_api(image_path)
    extraction_payload = {
        "extracted": extracted.model_dump(),
        "inferred": inferred.model_dump(),
        "visual": visual.model_dump(),
    }
    extraction_json = json.dumps(extraction_payload, indent=2, ensure_ascii=False)
    references_block = _format_references_block(references)
    criteria_json = json.dumps(criteria, indent=2, ensure_ascii=False)

    def _one() -> dict[str, Any]:
        return _judge_single(b64, media_type, extraction_json, references_block, criteria_json, criteria["category"])

    if n_passes == 1:
        passes = [_one()]
    else:
        with ThreadPoolExecutor(max_workers=n_passes) as pool:
            passes = list(pool.map(lambda _: _one(), range(n_passes)))

    axes = ["idea", "strategy", "execution", "impact"]

    # Average axis scores
    avg_scores: dict[str, float] = {}
    for axis in axes:
        scores = [p["axis_scores"][axis]["score"] for p in passes]
        avg_scores[axis] = round(statistics.mean(scores), 1)

    # Weighted score from averaged axis scores
    weights = {a["key"]: a["weight"] for a in criteria["axes"]}
    weighted = round(sum(avg_scores[axis] * weights[axis] for axis in axes), 1)

    # Average tier probabilities (entry-wise), renormalise
    avg_probs: dict[str, float] = {t: 0.0 for t in _TIERS}
    for p in passes:
        probs = p["tier_probabilities"]
        for t in _TIERS:
            avg_probs[t] += probs.get(t, 0.0)
    for t in _TIERS:
        avg_probs[t] /= len(passes)
    avg_probs = _normalise_probs(avg_probs)

    # Pick centroid pass for narrative consistency
    def _pass_distance(p: dict[str, Any]) -> float:
        return sum((p["tier_probabilities"].get(t, 0) - avg_probs[t]) ** 2 for t in _TIERS)

    centroid = min(passes, key=_pass_distance)

    return {
        "averaged_scores": avg_scores,
        "weighted_score": weighted,
        "tier_probabilities": avg_probs,
        "verdict": centroid["verdict"],
        "rationales": {axis: centroid["axis_scores"][axis]["rationale"] for axis in axes},
        "key_strengths": centroid.get("key_strengths", []),
        "key_weaknesses": centroid.get("key_weaknesses", []),
        "synthesis": centroid.get("synthesis", ""),
        "pairwise": {},
        "pass_scores": [
            {axis: p["axis_scores"][axis]["score"] for axis in axes} for p in passes
        ],
        "pass_probs": [p["tier_probabilities"] for p in passes],
    }
