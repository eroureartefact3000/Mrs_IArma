"""Malus rules from the project brief.

Three additive malus deductions on the LLM-judge weighted score:
  -10% if the board is not aesthetic (visual.craft_quality == "low")
  -20% if the client is not internationally known (user-provided flag)
  -20% if the agency is NOT part of one of six major networks (calibration 2026-05-29):
        Publicis, Havas, Omnicom (brief original) + WPP, IPG, Dentsu (calibration extension)

The list was extended from 3 to 6 holdings on 2026-05-29 after calibration showed
the original 3-only rule excluded too many legitimate winners (W+K London, Uncommon,
VML, Ogilvy, McCann etc.). The 6 holdings cover ~85% of Cannes Lions winners.

Detection is keyword-based against the agency string supplied by the user.
"""
from typing import Literal

from pydantic import BaseModel, Field

# Per-holding keyword tables, lowercase. Sub-agencies and notable brands grouped
# under each parent network. Non-exhaustive but covers the most common credits.
_HOLDING_KEYWORDS: dict[str, list[str]] = {
    "Publicis": [
        "publicis",
        "leo burnett",
        "saatchi & saatchi",
        "saatchi&saatchi",
        "saatchi",
        "bbh",
        "bartle bogle hegarty",
        "marcel",
        "razorfish",
        "digitas",
        "sapient",
        "msl",
        "starcom",
        "spark foundry",
        "epsilon",
        "zenith",
    ],
    "Havas": [
        "havas",
        "betc",
        "arnold",
        "conran",
    ],
    "Omnicom": [
        "bbdo",
        "ddb",
        "tbwa",
        "goodby silverstein",
        "goodby",
        "gsd&m",
        "gsd & m",
        "adam&eve",
        "adam & eve",
        "adam&eveddb",
        "omd",
        "hearts & science",
        "merkley",
        "fleishmanhillard",
        "fleishman",
        "porter novelli",
        "ketchum",
        "interbrand",
        "dm9",  # DM9 is now part of DDB (Omnicom)
    ],
    "WPP": [
        "wpp",
        "ogilvy",
        "grey",
        "wunderman",
        "jwt",
        "j. walter thompson",
        "j walter thompson",
        "akqa",
        "geometry",
        "hogarth",
        "vmly&r",
        "vml ",  # trailing space matters: catches "VML Prague", "VML Sydney" but not "VMLY&R" alone
        "vml,",
        "vml.",
        "vml-",
        "vml_",
        "vml/",
        "y&r",
        "groupm",
        "mindshare",
        "mediacom",
        "wavemaker",
        "mec ",
        "kantar",
        "burson",
        "cohn & wolfe",
    ],
    "IPG": [
        "ipg",
        "interpublic",
        "mccann",
        "fcb",
        "r/ga",
        "rga ",
        "initiative",
        "universal mccann",
        " um ",
        "mullenlowe",
        "mullen",
        "carmichael lynch",
        "weber shandwick",
        "golin",
        "acxiom",
        "octagon",
        "jack morton",
        "mediabrands",
        "dxtra",
    ],
    "Dentsu": [
        "dentsu",
        "carat",
        "iprospect",
        "merkle",
        "isobar",
        "360i",
        "vizeum",
        "posterscope",
        "mcgarrybowen",
        "gyro",
        "mktg",
    ],
}

Holding = Literal["Publicis", "Havas", "Omnicom", "WPP", "IPG", "Dentsu"]


def detect_holding(agency_name: str | None) -> Holding | None:
    """Return the holding (Publicis / Havas / Omnicom) that owns this agency, or None.

    Matches by case-insensitive substring against a curated keyword list.
    """
    if not agency_name:
        return None
    name = agency_name.lower()
    for holding, keywords in _HOLDING_KEYWORDS.items():
        if any(kw in name for kw in keywords):
            return holding  # type: ignore[return-value]
    return None


class MalusBreakdown(BaseModel):
    aesthetic_applied: bool = False
    client_applied: bool = False
    network_applied: bool = False
    detected_holding: Holding | None = None
    multiplier: float = Field(default=1.0, ge=0.0, le=1.0)
    notes: list[str] = Field(default_factory=list)


def compute_malus(
    *,
    craft_quality: Literal["high", "medium", "low"],
    agency_name: str | None,
    client_internationally_known: bool,
) -> MalusBreakdown:
    """Compute the additive malus and final multiplier.

    Multiplier is applied as: final_score = base_score * multiplier.
    Worst case: aesthetic + client + network all triggered = 0.50 multiplier.
    Best case: none triggered = 1.00 multiplier (no reduction).
    """
    breakdown = MalusBreakdown()

    if craft_quality == "low":
        breakdown.aesthetic_applied = True
        breakdown.notes.append("Aesthetic: craft_quality=low → -10%")

    if not client_internationally_known:
        breakdown.client_applied = True
        breakdown.notes.append("Client: not internationally known → -20%")

    holding = detect_holding(agency_name)
    breakdown.detected_holding = holding
    if holding is None:
        breakdown.network_applied = True
        breakdown.notes.append(
            f"Network: agency '{agency_name or '?'}' not detected in Publicis/Havas/Omnicom → -20%"
        )
    else:
        breakdown.notes.append(f"Network: agency belongs to {holding} → no malus")

    total_deduction = (
        (0.10 if breakdown.aesthetic_applied else 0.0)
        + (0.20 if breakdown.client_applied else 0.0)
        + (0.20 if breakdown.network_applied else 0.0)
    )
    breakdown.multiplier = max(0.0, 1.0 - total_deduction)
    return breakdown
