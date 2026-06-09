"""Phase 3 — Calibration test for PR (sweep #2, +10 boards).

Extends the first 10-board PR calibration to 20 total. Skips boards already
present in the output file so reruns are idempotent.

New batch composition (10 boards):
    2 Gold + 2 Silver + 4 Bronze (incl. 3 'above' rationales) + 2 Shortlist

Cost: ~$15-20. Runtime: ~8 min sequential. Appends to data_internal/calibration_pr_results.jsonl.
"""
from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter

from pipeline.evaluate import evaluate_board
from pipeline.schema import UserMetadata

ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT / "data_internal" / "calibration_pr_results.jsonl"


TEST_SET: list[dict] = [
    # ---- 2 Gold ----
    {
        "label": "[Hold-out Gold] Ketchup Fraud - Heinz",
        "image_path": ROOT / "2024" / "PR" / "GOLD" / "Ketchup Fraud - Heinz Ketchup (Rethink Toronto).jpg",
        "actual_tier": "Gold",
        "campaign": "Ketchup Fraud",
        "agency": "Rethink Toronto",
        "client": "Heinz",
        "client_international": True,
        "exclude_ids": {"ketchup-fraud-heinz-ketchup-rethink-toronto"},
    },
    {
        "label": "[Hold-out Gold] Translators - U.S. Bank",
        "image_path": ROOT / "2024" / "PR" / "GOLD" / "Translators - US Bank (McCann Detroit).jpg",
        "actual_tier": "Gold",
        "campaign": "Translators",
        "agency": "McCann Detroit",
        "client": "U.S. Bank",
        "client_international": False,  # US-only retail bank
        "exclude_ids": {"translators-us-bank-mccann-detroit"},
    },
    # ---- 2 Silver ----
    {
        "label": "[Hold-out Silver] Sing To Remember - Coca-Cola",
        "image_path": ROOT / "2024" / "PR" / "SILVER" / "Sing To Remember - Coca-Cola (VML, Mumbai).jpg",
        "actual_tier": "Silver",
        "campaign": "Sing To Remember",
        "agency": "VML Mumbai",
        "client": "Coca-Cola",
        "client_international": True,
        "exclude_ids": {"sing-to-remember-coca-cola-vml-mumbai"},
    },
    {
        "label": "[Hold-out Silver] SHT - IKEA",
        "image_path": ROOT / "2024" / "PR" / "SILVER" / "SHT - Ikea (Edelman Toronto).jpg",
        "actual_tier": "Silver",
        "campaign": "SHT (Second-Hand Tax)",
        "agency": "Edelman Toronto",
        "client": "IKEA",
        "client_international": True,
        "exclude_ids": {"sht-ikea-edelman-toronto"},
    },
    # ---- 4 Bronze (3 'above'-band rationales + 1 normal) ----
    {
        "label": "[Hold-out Bronze 'above'] Seemingly Ranch - Heinz",
        "image_path": ROOT / "2024" / "PR" / "BRONZE" / "Seemingly Ranch - Heinz Ketchup (Rethink Toronto).jpg",
        "actual_tier": "Bronze",
        "campaign": "Seemingly Ranch",
        "agency": "Rethink Toronto",
        "client": "Heinz",
        "client_international": True,
        "exclude_ids": {"seemingly-ranch-heinz-ketchup-rethink-toronto"},
    },
    {
        "label": "[Hold-out Bronze 'above'] Take My Lawyers - WOM",
        "image_path": ROOT / "2024" / "PR" / "BRONZE" / "Take My Lawyers - WOM (BBDO Colombia, Bogota).webp",
        "actual_tier": "Bronze",
        "campaign": "Take My Lawyers",
        "agency": "BBDO Colombia Bogota",
        "client": "WOM",
        "client_international": False,  # Colombian telco
        "exclude_ids": {"take-my-lawyers-wom-bbdo-colombia-bogota"},
    },
    {
        "label": "[Hold-out Bronze 'above'] Unsealed Books - Líra",
        "image_path": ROOT / "2024" / "PR" / "BRONZE" / "Unsealed Books - Líra (VML Hungary, Budapest).jpeg",
        "actual_tier": "Bronze",
        "campaign": "Unsealed Books",
        "agency": "VML Hungary Budapest",
        "client": "Líra",
        "client_international": False,  # Hungarian bookstore chain
        "exclude_ids": {"unsealed-books-líra-vml-hungary-budapest"},
    },
    {
        "label": "[Hold-out Bronze] Michael CeraVe - CeraVe",
        "image_path": ROOT / "2024" / "PR" / "BRONZE" / "Michael Cerave - Cerave (Ogilvy PR New York).webp",
        "actual_tier": "Bronze",
        "campaign": "Michael CeraVe",
        "agency": "Ogilvy PR New York",
        "client": "CeraVe",
        "client_international": True,  # L'Oréal-owned, international
        "exclude_ids": {"michael-cerave-cerave-ogilvy-pr-new-york"},
    },
    # ---- 2 Shortlist (not in index) ----
    {
        "label": "[Shortlist] After Dinner Dinner - McDonald's",
        "image_path": ROOT / "2024" / "PR" / "SHORTLIST" / "After Dinner Dinner - McDonald_s (FP7 McCann, Dubai).jpg",
        "actual_tier": "Shortlist",
        "campaign": "After Dinner Dinner",
        "agency": "FP7 McCann Dubai",
        "client": "McDonald's",
        "client_international": True,
        "exclude_ids": None,
    },
    {
        "label": "[Shortlist] El Carro Ford - Ford",
        "image_path": ROOT / "2024" / "PR" / "SHORTLIST" / "El Carro Ford - Ford (VML, Bogota).jpg",
        "actual_tier": "Shortlist",
        "campaign": "El Carro Ford",
        "agency": "VML Bogota",
        "client": "Ford",
        "client_international": True,
        "exclude_ids": None,
    },
]


TIER_RANK: dict[str, int] = {
    "Grand Prix": 5,
    "Gold": 4,
    "Silver": 3,
    "Bronze": 2,
    "Shortlist": 1,
    "Loser": 0,
    "No Medal": 0,
}


def _existing_labels() -> set[str]:
    if not OUT_PATH.exists():
        return set()
    return {json.loads(line)["label"] for line in OUT_PATH.open() if line.strip()}


def main() -> None:
    OUT_PATH.parent.mkdir(exist_ok=True)
    already_done = _existing_labels()
    todo = [c for c in TEST_SET if c["label"] not in already_done]
    print(f"Sweep #2: {len(todo)}/{len(TEST_SET)} boards to run (skipping {len(TEST_SET) - len(todo)} already done)")

    missing = [c["image_path"] for c in todo if not c["image_path"].exists()]
    if missing:
        print("⚠️  Missing files:")
        for p in missing:
            print(f"  - {p}")
        raise SystemExit(1)

    t_total = perf_counter()
    new_records: list[dict] = []
    for i, case in enumerate(todo, start=1):
        path: Path = case["image_path"]
        print(f"\n{'=' * 70}")
        print(f"[{i}/{len(todo)}] {case['label']}")
        print(f"  file : {path.relative_to(ROOT)}")
        print(f"  actual_tier : {case['actual_tier']}")

        metadata = UserMetadata(
            campaign_name=case["campaign"],
            agency=case["agency"],
            client=case["client"],
            category="PR",
            client_internationally_known=case["client_international"],
        )

        try:
            evaluation = evaluate_board(
                image_path=path,
                user_metadata=metadata,
                k_references=5,
                n_passes=3,
                verbose=False,
                exclude_ids=case.get("exclude_ids"),
            )
            tp = evaluation.tier_prediction
            record = {
                "label": case["label"],
                "actual_tier": case["actual_tier"],
                "predicted_tier": evaluation.predicted_tier,
                "tier_label": tp.tier_label,
                "score_percent": tp.score_percent,
                "confidence": tp.confidence,
                "base_score": evaluation.base_weighted_score,
                "final_score": evaluation.final_weighted_score,
                "tier_probabilities": evaluation.tier_probabilities,
                "axis_scores": {
                    "idea": evaluation.analysis.why_it_won.idea.score,
                    "strategy": evaluation.analysis.why_it_won.strategy.score,
                    "execution": evaluation.analysis.why_it_won.execution.score,
                    "impact": evaluation.analysis.why_it_won.impact.score,
                },
                "synthesis": tp.synthesis,
                "mystic_verdict": tp.mystic_verdict,
                "malus_multiplier": evaluation.malus["multiplier"],
                "exclude_ids": list(case["exclude_ids"]) if case.get("exclude_ids") else None,
            }
            tier_rank_actual = TIER_RANK.get(case["actual_tier"], -1)
            tier_rank_pred = TIER_RANK.get(evaluation.predicted_tier, -1)
            record["tier_distance"] = abs(tier_rank_actual - tier_rank_pred)
            new_records.append(record)

            print(f"  → predicted : {evaluation.predicted_tier} ({tp.score_percent}%, {tp.confidence})")
            print(f"  → axes      : I={record['axis_scores']['idea']}  S={record['axis_scores']['strategy']}  "
                  f"E={record['axis_scores']['execution']}  R={record['axis_scores']['impact']}")
            print(f"  → distance  : {record['tier_distance']}")
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            new_records.append({"label": case["label"], "actual_tier": case["actual_tier"], "error": str(e)})

    with OUT_PATH.open("a") as f:
        for r in new_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    elapsed = perf_counter() - t_total
    print(f"\n{'=' * 70}")
    print(f"✅ Sweep #2 done in {elapsed:.1f}s — {len(new_records)} new results appended to {OUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
