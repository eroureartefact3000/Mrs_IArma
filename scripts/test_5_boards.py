"""Run classify + extract pass1 + extract pass2 on 5 diverse boards.

This is the smoke test for the Phase 1 pipeline. ~$1-1.50 in API costs.
We pick 5 boards we have already eyeballed so we can compare model output to ground truth.

Usage (from project root):
    uv sync
    cp .env.example .env  # then edit .env with your ANTHROPIC_API_KEY
    uv run python test_5_boards.py
"""
from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter

from pipeline.classifier import classify
from pipeline.extractor import (
    compute_impact_strength,
    extract_pass1,
    extract_pass2,
    flag_for_review,
)
from pipeline.schema import BoardAnalysis

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

# 5 diverse boards (different tiers, categories, regions, visual styles).
# All were eyeballed manually so we can sanity-check the model output.
TEST_BOARDS: list[tuple[str, str]] = [
    (
        "Grand Prix",
        "Cannes-Lions-2025-PR-Grand-Prix-Indian-Railways-Lucky-Yatra-by-FCB-India-Mumbai.jpg",
    ),
    (
        "Grand Prix",
        "Outdoor-Grand-Prix-at-Cannes-Lions-2025-KitKat-Nestle-Crowd-Street-Public-Transport-VML-Prague-1.jpeg",
    ),
    ("Gold", "Burger-King-Happiness-Cannes-Lions-JUIN20254-1024x732.png"),
    ("Silver", "855-HOW-TO-QUIT-(OPIOIDS) – ANZEN HEALTH (SERVICEPLAN GERMANY).jpg"),
    ("Bronze", "CHILD WEDDING CARDS – UN WOMEN (IMPACT BBDO DUBAI).jpg"),
]


def slug(path: Path) -> str:
    return path.stem.lower().replace(" ", "-").replace("–", "-").replace("(", "").replace(")", "")[:80]


def run_one(tier: str, filename: str) -> dict | None:
    path = ROOT / "2025" / tier / filename
    print(f"\n=== [{tier}] {filename} ===")
    if not path.exists():
        print(f"  ! File not found: {path}")
        return None

    t0 = perf_counter()
    print("  [1/3] classify...")
    cls = classify(path)
    print(f"        category={cls['category']} ({cls['confidence']}) — {cls['reasoning']}")

    print("  [2/3] extract pass 1 (literal)...")
    extracted = extract_pass1(path)
    print(f"        campaign={extracted.campaign!r} brand={extracted.brand!r}")
    print(
        f"        non-null fields: "
        f"tagline={extracted.tagline is not None} "
        f"context={extracted.context is not None} "
        f"insight={extracted.insight is not None} "
        f"idea={extracted.idea is not None} "
        f"execution={len(extracted.execution)} "
        f"metrics={len(extracted.metrics)} "
        f"press={len(extracted.press_coverage)}"
    )

    print("  [3/3] extract pass 2 (inferred + visual)...")
    inferred, visual = extract_pass2(path, extracted)
    print(f"        one_liner: {inferred.one_liner!r}")
    print(f"        mechanisms: {inferred.creative_mechanisms}")
    print(f"        craft_quality: {visual.craft_quality}")

    impact = compute_impact_strength(extracted, inferred)
    flag, reasons = flag_for_review(extracted, inferred)
    print(f"        impact_strength: {impact}")
    if flag:
        print(f"  ⚠️  FLAGGED FOR REVIEW: {reasons}")

    analysis = BoardAnalysis(
        id=slug(path),
        tier=tier,  # type: ignore[arg-type]
        category=cls["category"],
        category_confidence=cls["confidence"],
        category_reasoning=cls.get("reasoning"),
        file_path=str(path.relative_to(ROOT)),
        extracted=extracted,
        inferred=inferred,
        visual=visual,
        impact_strength=impact,
        review_flag=flag,
        review_reasons=reasons,
    )

    elapsed = perf_counter() - t0
    print(f"  ⏱ {elapsed:.1f}s")
    return analysis.model_dump()


def main() -> None:
    results: list[dict] = []
    for tier, filename in TEST_BOARDS:
        try:
            r = run_one(tier, filename)
            if r is not None:
                results.append(r)
        except Exception as e:  # noqa: BLE001
            print(f"  ❌ ERROR: {type(e).__name__}: {e}")

    out_path = DATA_DIR / "test_5_boards.json"
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"\n✅ Wrote {len(results)} extractions to {out_path}")


if __name__ == "__main__":
    main()
