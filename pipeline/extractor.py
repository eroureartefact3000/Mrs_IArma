"""Two-pass extraction of a board into the v3 schema.

Pass 1 (strict): only fields that are literally on the board. Null otherwise.
Pass 2 (inferred): fills the strictly-missing fields when confident, always
produces a one-liner + creative_mechanisms tags + visual signals.
"""
import json
from pathlib import Path

from pydantic import ValidationError

from .client import call_vision, extract_json
from .images import load_image_for_api
from .schema import Extracted, ImpactStrength, Inferred, Visual

_MAX_RETRIES = 2

_EXTRACT_PASS1 = """You are extracting structured information from a Cannes Lions winner board (digital presentation image, one-pager).

STRICT RULES:
1. For text fields (campaign, brand, tagline, context, insight, idea): fill only if EXPLICITLY visible as text. If not present, return null. NEVER invent or paraphrase missing content.
2. EXCEPTION — execution: include items shown in an unambiguous visual strip / thumbnail row that depicts campaign placements (OOH photos, gameplay screenshots, app screens, product mockups, in-context campaign moments). Describe each concisely in text. Leave [] only if the board shows nothing of the execution.
3. Paraphrase tightly when text is long. Don't copy full paragraphs verbatim.
4. For metrics, keep unit + number ("$685M revenue", "560M impressions", "+5.4 p.p. engagement"). If a number is visible but its unit is unreadable, omit it.
5. Output language: English (paraphrase if the board uses another language).

Schema (return EXACTLY this structure):
{
  "campaign": "string or null - campaign name as printed",
  "brand": "string or null - the advertiser/brand",
  "agencies": ["list of agency names if visible on the board itself - empty if not"],
  "tagline": "string or null - the main headline/tagline of the board",
  "context": "string or null - the problem/challenge/background, max 300 chars",
  "insight": "string or null - the consumer/cultural insight if stated",
  "idea": "string or null - the creative idea in 1-2 sentences",
  "execution": ["list of bullet points - channels/mechanics from labelled text OR unambiguous visual strips"],
  "metrics": ["list of result stats with unit + number - empty if no readable quantified results"],
  "press_coverage": ["list of press outlets cited or short quotes - empty if no press logos/quotes"]
}

Return ONLY the JSON object, no markdown fences, no commentary."""


_EXTRACT_PASS2 = """You have already extracted the explicit content of a Cannes Lions winner board. Now infer the missing pieces and analyse visual style.

Here is what was extracted from the board (the literal pass):
{extracted_json}

Your tasks:
1. For "context", "insight", and "idea": if the extracted version is null, infer from the visuals + other extracted fields when confident. If extracted was already filled, return null here (we ONLY infer what was missing in the literal pass).
2. ALWAYS produce "one_liner": a maximally punchy headline-style sentence summarising the core idea.
   HARD CONSTRAINTS:
   - 12 words MAX. Shorter is better.
   - No gerunds, no participial phrases ("turning…", "making…", "letting…").
   - No mention of metric numbers or results.
   - Prefer simple noun-phrase or "X IS Y" / "X becomes Y" structures.
   Good examples (copy this style):
   - "The train ticket IS the lottery ticket."
   - "The pill in your hand becomes the helpline."
   - "Real wedding invitations, drawn by children."
   - "Two players named Burger and King hijacked every match."
   Bad examples (avoid):
   - "Every train ticket became a lottery ticket, turning fare evasion into a chance to win."  (too long, gerund)
   - "Hand a KitKat to someone glued to their phone — and give 'Have a Break' a whole new meaning."  (multi-clause)
3. ALWAYS produce "creative_mechanisms": 2-4 free-text lowercase-with-hyphens tags identifying the type of creative move. Examples:
   - "everyday-object-transformation"
   - "celebrity-as-prop"
   - "ambient-media-hijack"
   - "data-as-content"
   - "platform-jailbreak"
   - "ritual-creation"
   - "absurd-product-line"
   - "cultural-symbol-subversion"
   - "purpose-driven-product"
4. "qualitative_summary": ALWAYS produce a 1-2 sentence narrative summary of the campaign's impact, regardless of whether metrics are present. Capture the cultural / behavioural / legislative / brand outcome in plain English. Examples: "Reframed fare-paying as a culturally desirable act of luck-seeking, shifting national commuter behaviour." / "Triggered a parliamentary dialogue in Pakistan's National Assembly; anchored a draft bill." This field feeds the RAG with a human-readable impact signal.
5. Visual analysis (ALWAYS required):
   - "style_description": describe visual style in 1-2 sentences (composition, photo vs illustration, density, tone)
   - "craft_quality": "high" (polished award-grade craft), "medium" (clean, professional but not exceptional), or "low" (visibly amateur, rushed, or weak typography/layout)
   - "dominant_colors": 2-4 dominant colors (plain names: red, black, navy, beige, etc.)

Return ONLY this JSON, nothing else:
{{
  "context": "<inferred or null>",
  "insight": "<inferred or null>",
  "idea": "<inferred or null>",
  "one_liner": "...",
  "creative_mechanisms": ["...", "..."],
  "qualitative_summary": "<1-2 sentence narrative of impact>",
  "visual": {{
    "style_description": "...",
    "craft_quality": "high|medium|low",
    "dominant_colors": ["...", "..."]
  }}
}}"""


def extract_pass1(image_path: Path) -> Extracted:
    b64, media_type = load_image_for_api(image_path)
    last_err: Exception | None = None
    for _ in range(_MAX_RETRIES + 1):
        raw = call_vision(_EXTRACT_PASS1, b64, media_type, max_tokens=1500)
        try:
            return Extracted(**extract_json(raw))
        except (json.JSONDecodeError, ValidationError) as e:
            last_err = e
    raise last_err  # type: ignore[misc]


def extract_pass2(image_path: Path, extracted: Extracted) -> tuple[Inferred, Visual]:
    b64, media_type = load_image_for_api(image_path)
    prompt = _EXTRACT_PASS2.format(extracted_json=extracted.model_dump_json(indent=2))
    last_err: Exception | None = None
    for _ in range(_MAX_RETRIES + 1):
        raw = call_vision(prompt, b64, media_type, max_tokens=1500)
        try:
            data = extract_json(raw)
            inferred = Inferred(
                context=data.get("context"),
                insight=data.get("insight"),
                idea=data.get("idea"),
                one_liner=data.get("one_liner"),
                creative_mechanisms=data.get("creative_mechanisms", []),
                qualitative_summary=data.get("qualitative_summary"),
            )
            visual = Visual(**data["visual"])
            return inferred, visual
        except (json.JSONDecodeError, ValidationError, KeyError) as e:
            last_err = e
    raise last_err  # type: ignore[misc]


def compute_impact_strength(extracted: Extracted, inferred: Inferred) -> ImpactStrength:
    """Derive an overall impact-strength label from the structured evidence.

    Used downstream by the RAG to weight references by reliability, and by the
    judge to calibrate the "Results" axis.
    """
    n_metrics = len(extracted.metrics)
    n_press = len(extracted.press_coverage)

    if n_metrics >= 2:
        return "strong"
    if n_metrics >= 1 or n_press >= 3:
        return "moderate"
    if n_press > 0:
        return "moderate"
    if inferred.qualitative_summary:
        return "qualitative_only"
    return "none"


def flag_for_review(extracted: Extracted, inferred: Inferred) -> tuple[bool, list[str]]:
    """Identify boards where the extraction is too weak to trust in the RAG base.

    Critical single-trigger flag: zero impact evidence anywhere (no metrics, no
    press, no qualitative outcome). Otherwise, two or more soft signals.
    """
    reasons: list[str] = []
    if not extracted.campaign:
        reasons.append("campaign name missing")
    if not extracted.brand:
        reasons.append("brand missing")
    if not extracted.idea and not inferred.idea:
        reasons.append("idea missing in both passes")
    if not extracted.execution:
        reasons.append("no execution detail")

    no_impact = (
        not extracted.metrics
        and not extracted.press_coverage
        and not inferred.qualitative_summary
    )
    if no_impact:
        reasons.append("no impact evidence (no metrics, no press, no qualitative outcome)")
        return True, reasons

    return len(reasons) >= 2, reasons
