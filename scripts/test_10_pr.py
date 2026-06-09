"""Run the pipeline on ~10 boards strongly suspected to be PR.

Strategy:
1. Pre-classify ~13 candidates (selected by filename heuristic: news, gov, NGO, activism).
2. Keep only those the classifier confirms as PR.
3. Run full extraction on up to 10 of them.
4. Print a side-by-side summary so we can spot cross-board consistency issues.

Cost: ~13 classify (~$0.30) + ~10 full extract (~$2) = ~$2.30
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

# 13 candidates chosen by filename heuristic — news, gov, NGO, brand activism, etc.
CANDIDATES: list[tuple[str, str]] = [
    ("Gold", "INK OF DEMOCRACY – TIMES OF INDIA GROUP (HAVAS MUMBAI).jpg"),
    ("Gold", "THE NEW PRESIDENT – ANNAHAR NEWSPAPER (IMPACT BBDO DUBAI).webp"),
    ("Gold", "HUMANIMAL TOURISM – PROCOLOMBIA (DDB COLOMBIA).webp"),
    ("Gold", "DAISY VS SCAMMERS – O2 (VCCP LONDON).jpg"),
    ("Silver", "ANNAHAR’S ACTIVE JOURNALISM – ANNAHAR (IMPACT BBDO DUBAI).webp"),
    ("Silver", "THE SHOOTING – LA UNIÓN NEWSPAPER (GREY MEXICO).webp"),
    ("Silver", "LOVE CAPTURED – THE EXODUS ROAD (KLICK HEALTH TORONTO).png"),
    ("Silver", "#SHARETHELOAD 10 YEARS – PROCTER & GAMBLE (BBDO INDIA MUMBAI).jpg"),
    ("Silver", "1837 TIFFANY BLUE CONSERVATION TIFFANY & CO L&C NEW YORK Cannes Lions Board.webp"),
    ("Bronze", "HER DOME – GOVERNMENT OF THE STATE OF SÃO PAULO (DPZ SÃO PAULO).webp"),
    ("Bronze", "UNFREEZE MY RIGHTS – AWAKENING FOUNDATION (DENTSU CREATIVE TAIPEI).jpeg"),
    ("Bronze", "THE FREEDOM EDITION – SOCIETY (BETC PARIS).jpg"),
    ("Bronze", "CHEERING FOR THE RAIN – SENNA POR AYRTON (ARTPLAN SÃO PAULO).jpg"),
]


def slug(path: Path) -> str:
    return (
        path.stem.lower()
        .replace(" ", "-")
        .replace("–", "-")
        .replace("(", "")
        .replace(")", "")[:80]
    )


def main() -> None:
    t_start = perf_counter()

    # === Step 1: classify all candidates ===
    print(f"=== Step 1/3: classify {len(CANDIDATES)} candidates ===\n")
    classified: list[tuple[str, str, dict]] = []
    for tier, filename in CANDIDATES:
        path = ROOT / "2025" / tier / filename
        if not path.exists():
            print(f"  ! Missing: {filename}")
            continue
        try:
            cls = classify(path)
            label = "✓ PR " if cls["category"] == "PR" else f"✗ {cls['category']}"
            print(f"  {label:30s} [{cls['confidence']}] {filename[:60]}")
            classified.append((tier, filename, cls))
        except Exception as e:  # noqa: BLE001
            print(f"  ❌ classify failed: {filename} — {type(e).__name__}: {e}")

    pr_only = [c for c in classified if c[2]["category"] == "PR"]
    print(f"\n  → {len(pr_only)} / {len(classified)} confirmed as PR\n")

    pr_only = pr_only[:10]

    # === Step 2: full extraction on PR-confirmed ===
    print(f"=== Step 2/3: full extraction on {len(pr_only)} PR boards ===\n")
    results: list[dict] = []
    for tier, filename, cls in pr_only:
        path = ROOT / "2025" / tier / filename
        print(f"  > {filename[:60]}")
        try:
            extracted = extract_pass1(path)
            inferred, visual = extract_pass2(path, extracted)
            impact = compute_impact_strength(extracted, inferred)
            flag, reasons = flag_for_review(extracted, inferred)
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
            results.append(analysis.model_dump())
            print(
                f"      campaign={extracted.campaign!r:30s} impact={impact} "
                f"flag={'⚠️' if flag else 'ok'}"
            )
        except Exception as e:  # noqa: BLE001
            print(f"      ❌ extract failed: {type(e).__name__}: {e}")

    # === Step 3: save + summary ===
    out_path = DATA_DIR / "pr_10.json"
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    elapsed = perf_counter() - t_start
    print(f"\n=== Step 3/3: done in {elapsed:.0f}s — wrote {len(results)} to {out_path} ===")

    # Quick cross-board sanity prints
    print("\n--- One-liners (concision check) ---")
    for r in results:
        ol = r["inferred"]["one_liner"]
        words = len((ol or "").split())
        marker = "  " if words <= 12 else "⚠️"
        print(f"  {marker} [{words:2d}w] {ol}")

    print("\n--- Impact strength distribution ---")
    from collections import Counter

    counts = Counter(r["impact_strength"] for r in results)
    for k, v in counts.most_common():
        print(f"  {k}: {v}")

    print("\n--- Flagged for review ---")
    for r in results:
        if r["review_flag"]:
            print(f"  ⚠️  {r['id']}: {r['review_reasons']}")


if __name__ == "__main__":
    main()
