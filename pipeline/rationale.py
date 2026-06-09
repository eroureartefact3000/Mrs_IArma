"""Generate a structured 'why-it-won' rationale for a Cannes Lions board.

Two key principles enforced in the prompt (from DA feedback 2026-05-19):

1. STRICT SEPARATION OF STRATEGY AND EXECUTION
   - Strategy = WHY: (a) who is the brand + idea-mission fit, (b) insight veracity
   - Execution = HOW: orchestration + media-target fit + amplification
   No bleeding between the two axes.

2. SCORE DISCRIMINATION
   - Score each axis on absolute craft, not normalised to tier band.
   - Two boards in the same tier can legitimately differ by 10-15 points if
     their crafts differ.
   - For winners we still provide the expected band as soft guidance; for
     Shortlist/Loser we tell the model what the label means and let scores fall.

The function is now PARAMETRIC: pass the criteria dict for any category
(PR / Outdoor / etc.) and tier-band helpers.
"""
import json
from typing import Any, Callable

from pydantic import ValidationError

from .client import MODEL, extract_json, get_client
from .schema import AxisScore, Extracted, Inferred, Tier, Visual, WhyItWon

_MAX_RETRIES = 2


# Winning tiers and not — for the prompt
_WINNING = {"Grand Prix", "Gold", "Silver", "Bronze"}

_TIER_GUIDANCE = {
    "Shortlist": (
        "This board PASSED the first jury screening (a quality sanity check) but DID NOT "
        "medal. It is competent work but the jury did not award it a Lion. Expect total "
        "weighted score in the 35-55 range (just below the Bronze threshold of 50)."
    ),
    "Loser": (
        "This board DID NOT make the jury shortlist — it failed even the first quality "
        "screening. Score it accordingly: expect a total weighted score under 35."
    ),
}


_PROMPT = """You are a Cannes Lions {category} jury member analysing an entry retrospectively.

Your task: explain WHY this board obtained its specific result (medal, shortlist, or no shortlist) by scoring it on the four axes and writing per-axis rationales grounded in the visible evidence.

== THE CAMPAIGN ==
{extraction_json}

== THE OUTCOME ==
This entry's outcome at Cannes Lions: **{tier}**.
{tier_guidance}

== JUDGING CRITERIA ({category}) ==
{criteria_json}

== HARD RULES ==

STRATEGY axis = WHY (and ONLY why). You must structure the strategy rationale to answer, in this order:
  1. WHO IS THE BRAND? Identify the brand and its mission. If the brand is not internationally known, name it explicitly and describe what it stands for. Many great PR-style campaigns are by local associations, NGOs, or category-niche brands.
  2. Is the idea coherent with that brand's mission?
  3. Are the context and insights real, verifiable, and data-backed? Cite the specific data points the board uses (numbers, studies, cultural facts).
  Do NOT discuss orchestration, media choices, channels, or amplification under Strategy.

EXECUTION axis = HOW (and ONLY how). Structure the execution rationale to answer:
  - Are the means and media chosen relevant to the objective and the target?
  - What were the phases of the campaign? (e.g. launch → press pickup → partnership → amplification)
  - Which channels were used and were they the right ones for the audience?
  - Were there amplification layers (PR loops, partnerships, social rebroadcast, brand coalitions, real-world events)?
  Do NOT discuss brand mission, insight quality, or context veracity under Execution.

SCORE DISCRIMINATION: judge each axis on ABSOLUTE CRAFT, not relative to tier band. Two boards in the same tier can legitimately differ by 10-15 points per axis if their crafts genuinely differ. Resist the urge to flatten scores into the expected band — score the craft, let the total fall where it does.

RIGOUR & SKEPTICISM (apply systematically — agencies stage their results):

1. PERCENTAGES WITHOUT BASE. When the board cites a percentage gain (e.g. "+50%", "+39,285%"), explicitly ask in the rationale: "X% of what?". Look in the extracted metrics for the absolute base. If the base is missing, treat the percentage as a soft claim, NOT a strong impact proof. Example to imitate: "The board reports '50% of featured dogs adopted' but does not disclose the cohort size, so the figure is unanchored." Penalise Impact score when key percentages are unbased.

2. UNVERIFIED PRESS / NUMBERS. Treat press logos and large reach figures (impressions, viewership, share-of-voice) as CLAIMS made by the entrant, not verified facts. If a rationale rests on "300M impressions" or "covered by CNN", explicitly flag the load-bearing claim in your wording (e.g. "if the cited 303M impressions hold up..."). Do not award maximal Impact scores on the strength of unverifiable press claims alone.

3. MISSING REAL BUSINESS OUTCOME. First, identify the brand's likely business objective for this specific campaign (sales / sign-ups / viewership lift / behaviour change / footfall / category share). Then check whether the board actually demonstrates THAT outcome — not a surrogate. Surrogate metrics (impressions, reach, sentiment) are weaker than business outcomes. If the obvious business outcome is conspicuously absent from the board, the Impact score must reflect that absence even if the surface metrics are impressive.

4. NO VAGUE SUPERLATIVES. Words like "exceptional", "extraordinary", "world-first", "unprecedented", "best-ever" must be IMMEDIATELY followed by the concrete observation that justifies them. If you can't justify the superlative with a specific, board-visible fact, drop the word. Example: instead of "exceptional craft", write "the AI-restored shelter-dog portraits raise amateur source material to brand-campaign polish — exceptional in that specific transformation."

5. CULTURAL / LINGUISTIC PRECISION. When a campaign relies on wordplay, sports references, political signs or cultural shorthand, identify the precise scope: a Québec-only joke is not Canada-wide; a Mexico-City reference is not pan-LATAM; a UK gambling jargon is not US-readable. Mention the scope explicitly in the rationale (e.g. "the 'Buuuud' chant is a Francophone-Québec wordplay around 'Les Canadiens' — not pan-Canadian").

VERDICT: one decisive sentence naming THE single thing that made (or didn't make) this work win its Lion — what a juror would say first in the room. No generic praise.

== YOUR DELIVERABLE ==
Return STRICT JSON with this exact shape, nothing else:

{{
  "idea":      {{ "score": <int 0-100>, "rationale": "<2-3 sentences>" }},
  "strategy":  {{ "score": <int 0-100>, "rationale": "<2-3 sentences following the 3-step WHO/mission-fit/insight-veracity structure>" }},
  "execution": {{ "score": <int 0-100>, "rationale": "<2-3 sentences describing orchestration + media-target fit>" }},
  "impact":    {{ "score": <int 0-100>, "rationale": "<2-3 sentences citing specific results>" }},
  "verdict": "<1-2 sentence punchline: the single biggest reason this got its result>"
}}"""


def _build_tier_guidance(tier: Tier, expected_range: tuple[int, int] | None) -> str:
    if tier in _WINNING and expected_range is not None:
        low, high = expected_range
        return (
            f"Expected weighted-score band for a {tier} entry (from the project brief): {low}-{high}. "
            "Use this as soft calibration only — do not flatten scores to fit, score the craft on its merits."
        )
    return _TIER_GUIDANCE.get(tier, "")


def generate_why_it_won(
    extracted: Extracted,
    inferred: Inferred,
    visual: Visual,
    tier: Tier,
    criteria: dict[str, Any],
    expected_range_fn: Callable[[Tier], tuple[int, int] | None],
    tier_consistency_fn: Callable[[Tier, float], str],
) -> WhyItWon:
    """Run the rationale generator. The criteria + tier helpers are passed in
    so the same function can be used for PR, Outdoor, Health, etc.
    """
    expected = expected_range_fn(tier)
    tier_guidance = _build_tier_guidance(tier, expected)

    extraction_payload = {
        "extracted": extracted.model_dump(),
        "inferred": inferred.model_dump(),
        "visual": visual.model_dump(),
    }
    prompt = _PROMPT.format(
        category=criteria["category"],
        extraction_json=json.dumps(extraction_payload, indent=2, ensure_ascii=False),
        criteria_json=json.dumps(criteria, indent=2, ensure_ascii=False),
        tier=tier,
        tier_guidance=tier_guidance,
    )

    client = get_client()
    last_err: Exception | None = None
    for _ in range(_MAX_RETRIES + 1):
        msg = client.messages.create(
            model=MODEL,
            max_tokens=1600,
            messages=[{"role": "user", "content": prompt}],
        )
        try:
            data: dict[str, Any] = extract_json(msg.content[0].text)
            axes = {k: AxisScore(**data[k]) for k in ("idea", "strategy", "execution", "impact")}
            weights = {axis["key"]: axis["weight"] for axis in criteria["axes"]}
            weighted = sum(axes[k].score * weights[k] for k in axes)
            return WhyItWon(
                idea=axes["idea"],
                strategy=axes["strategy"],
                execution=axes["execution"],
                impact=axes["impact"],
                weighted_score=round(weighted, 1),
                verdict=data["verdict"],
                tier_consistency=tier_consistency_fn(tier, weighted),  # type: ignore[arg-type]
            )
        except (json.JSONDecodeError, ValidationError, KeyError, TypeError) as e:
            last_err = e
    raise last_err  # type: ignore[misc]
