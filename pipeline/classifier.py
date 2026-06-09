"""Pre-classify a board into a Cannes Lions family/category.

Used to filter the ~358 winning boards down to the PR subset before running
the full v3 extraction. Cheap call (~$0.01-0.02 per board).
"""
import json
from pathlib import Path

from .client import call_vision, extract_json
from .images import load_image_for_api

_MAX_RETRIES = 2

CLASSIFY_PROMPT = """You are a Cannes Lions categorisation expert.

Look at this digital presentation board (one-pager that summarises a Cannes Lions campaign entry) and identify which Cannes Lions family/category it was most likely entered in.

Cannes Lions families & categories:
- Brand: Creative Brand
- Classic: Audio & Radio, Film, Outdoor, Print & Publishing
- Craft: Design, Digital Craft, Film Craft, Industry Craft
- Engagement: Creative B2B, Creative Data, Direct, Media, PR, Social & Creator
- Entertainment: Entertainment, Entertainment for Gaming, Entertainment for Music, Entertainment for Sport
- Experience: Brand Experience & Activation, Creative Business Transformation, Creative Commerce, Innovation, Luxury
- Good: Glass (The Lion for Change), Sustainable Development Goals
- Health: Health & Wellness, Pharma
- Strategy: Creative Effectiveness, Creative Strategy
- Titanium

Signals to look for:
- Explicit category mentions on the board (sometimes printed)
- The nature of the work: PR-led story vs craft-led visual vs gaming integration etc.
- Metric types: press impressions => PR; sales => Commerce; viewers/engagement => Entertainment; behavior change => SDG/Glass
- Visual structure: press logos + journalist quotes => PR; OOH photo strip => Outdoor; gameplay screenshots => Gaming

PR specifically: campaigns that earn public/media attention, generate press coverage, drive cultural conversation, restore or build reputation. Boards typically show press logos, journalist quotes, impressions metrics, "as covered by" sections.

CRITICAL TIEBREAK RULES (apply in order, before deciding):
1. Outdoor vs Print & Publishing: if the board shows photographs of placements in public space (transit vehicles, bus shelters, billboards, street furniture, building wraps, tram or station ads, installations), the answer is OUTDOOR — even if the headline mentions "photography", "print", or "poster", and even if the medium itself is a printed sheet. Print & Publishing only applies when the work IS a printed editorial product (magazine, newspaper insert, book, packaging-as-medium) consumed as a printed artefact, not when a printed creative is placed in a public space.
2. PR vs Direct: if the campaign explicitly says "direct mail to X" or targets a specific named audience with a measurable response mechanic, the answer is DIRECT. PR targets the general public/press at scale.
3. Health & Wellness vs PR: if a healthcare brand or non-profit drives a public health behaviour change and the impact metric is "lives reached" / "calls received" / "behaviour shifted", prefer HEALTH & WELLNESS unless press coverage is the dominant story.
4. Entertainment for Gaming vs Entertainment for Sport: integrations INSIDE a video game (FIFA / EA FC, Fortnite, Roblox, etc.) = GAMING, even when the game's theme is sport. SPORT applies to real-world athletes, leagues, or live sports broadcasts.
5. SDG / Glass vs Direct vs PR: purpose-driven campaigns can fit several. If the mechanic is a direct-mail or targeted action with a named recipient, prefer DIRECT. If the work earned mass press attention, prefer PR. Reserve SDG / Glass for entries whose ENTIRE thesis is the social-impact framing (UN goal alignment, gender equality, climate, etc.) without a stronger discipline-specific mechanic.

A campaign can win in several categories. Return the MOST LIKELY primary category based on what the board emphasises, applying the tiebreak rules above when in doubt.

Return ONLY this JSON, nothing else:
{"category": "<exact name from list>", "confidence": "high|medium|low", "reasoning": "<one short sentence>"}"""


def classify(image_path: Path) -> dict:
    b64, media_type = load_image_for_api(image_path)
    last_err: Exception | None = None
    for _ in range(_MAX_RETRIES + 1):
        raw = call_vision(CLASSIFY_PROMPT, b64, media_type, max_tokens=300)
        try:
            return extract_json(raw)
        except json.JSONDecodeError as e:
            last_err = e
    raise last_err  # type: ignore[misc]
