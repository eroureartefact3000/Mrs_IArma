"""Phase 3 — Calibration test for Print & Publishing.

11-board stratified set: 1 GP + 2 Gold + 2 Silver + 3 Bronze (hold-out, exclude_ids
self-id) + 3 Shortlist (truly held out).

Cost: ~$15-20. Runtime: ~8 min sequential.
"""
from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter

from pipeline.evaluate import evaluate_board
from pipeline.schema import UserMetadata

ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT / "data_internal" / "calibration_print_results.jsonl"


TEST_SET: list[dict] = [
    {
        "label": "[Hold-out GP] Recycle Me - Coca-Cola",
        "image_path": ROOT / "2024" / "PRINT&PUBLISHING" / "GRAND PRIX" / "Recycle Me - Coca Cola (Ogilvy, New York).jpeg",
        "actual_tier": "Grand Prix",
        "campaign": "Recycle Me",
        "agency": "Ogilvy New York",
        "client": "Coca-Cola",
        "client_international": True,
        "exclude_ids": {"recycle-me-coca-cola-ogilvy-new-york"},
    },
    {
        "label": "[Hold-out Gold] Braided History - L'Oréal Puerto Rico",
        "image_path": ROOT / "2024" / "PRINT&PUBLISHING" / "GOLD" / "Braided History - L_oréal de Puerto Rico (DDB Latin Puerto Rico).webp",
        "actual_tier": "Gold",
        "campaign": "Braided History",
        "agency": "DDB Latin Puerto Rico",
        "client": "L'Oréal Puerto Rico",
        "client_international": True,
        "exclude_ids": {"braided-history-l-oréal-de-puerto-rico-ddb-latin-puerto-rico"},
    },
    {
        "label": "[Hold-out Gold] Find Your Summer - Magnum",
        "image_path": ROOT / "2024" / "PRINT&PUBLISHING" / "GOLD" / "Find Your Summer - Magnum (Lola Mullenlowe, Madrid).jpeg",
        "actual_tier": "Gold",
        "campaign": "Find Your Summer",
        "agency": "Lola Mullenlowe Madrid",
        "client": "Magnum",
        "client_international": True,
        "exclude_ids": {"find-your-summer-magnum-lola-mullenlowe-madrid"},
    },
    {
        "label": "[Hold-out Silver] The AI President - Annahar",
        "image_path": ROOT / "2024" / "PRINT&PUBLISHING" / "SILVER" / "The AI President - Annahar Newspaper (Impact BBDO, Dubai).jpg",
        "actual_tier": "Silver",
        "campaign": "The AI President",
        "agency": "Impact BBDO Dubai",
        "client": "Annahar Newspaper",
        "client_international": False,  # Lebanese newspaper
        "exclude_ids": {"the-ai-president-annahar-newspaper-impact-bbdo-dubai"},
    },
    {
        "label": "[Hold-out Silver] Unfinished - EE",
        "image_path": ROOT / "2024" / "PRINT&PUBLISHING" / "SILVER" / "Unfinished - EE (Saatchi & Saatchi London).jpg",
        "actual_tier": "Silver",
        "campaign": "Unfinished",
        "agency": "Saatchi & Saatchi London",
        "client": "EE",
        "client_international": False,  # UK mobile network
        "exclude_ids": {"unfinished-ee-saatchi-saatchi-london"},
    },
    {
        "label": "[Hold-out Bronze] 10 vs 10 - Dove",
        "image_path": ROOT / "2024" / "PRINT&PUBLISHING" / "BRONZE" / "10 vs 10 - Dove (Ogilvy, London _ Ogilvy, Sydney).jpeg",
        "actual_tier": "Bronze",
        "campaign": "When did 10 stop looking like 10?",
        "agency": "Ogilvy London",
        "client": "Dove",
        "client_international": True,
        "exclude_ids": {"10-vs-10-dove-ogilvy-london-ogilvy-sydney"},
    },
    {
        "label": "[Hold-out Bronze] 1943 - Robert Capa",
        "image_path": ROOT / "2024" / "PRINT&PUBLISHING" / "BRONZE" / "1943 - Robert Capa (Innocean Berlin).webp",
        "actual_tier": "Bronze",
        "campaign": "Capa vs War",
        "agency": "Innocean Berlin",
        "client": "Robert Capa Contemporary Photography Center",
        "client_international": False,  # Budapest cultural institution
        "exclude_ids": {"1943-robert-capa-innocean-berlin"},
    },
    {
        "label": "[Hold-out Bronze] A Soup To Remember - Marodi",
        "image_path": ROOT / "2024" / "PRINT&PUBLISHING" / "BRONZE" / "A Soup To Remember - Marodi (Bruketa&Zinic&Grey, Zagreb).webp",
        "actual_tier": "Bronze",
        "campaign": "A Soup To Remember",
        "agency": "Bruketa & Zinic & Grey Zagreb",
        "client": "Marodi",
        "client_international": False,  # Croatian soup brand
        "exclude_ids": {"a-soup-to-remember-marodi-bruketa-zinic-grey-zagreb"},
    },
    # ---- Shortlists (not in index) ----
    {
        "label": "[Shortlist] Twiggy Full Circle - eBay",
        "image_path": ROOT / "2024" / "PRINT&PUBLISHING" / "SHORTLIST" / "Twiggy Full Circle - Ebay (Essencemediacom, New York).jpeg",
        "actual_tier": "Shortlist",
        "campaign": "Twiggy Full Circle",
        "agency": "EssenceMediacom New York",
        "client": "eBay",
        "client_international": True,
        "exclude_ids": None,
    },
    {
        "label": "[Shortlist] Child Wedding Cards - UN Women",
        "image_path": ROOT / "2024" / "PRINT&PUBLISHING" / "SHORTLIST" / "Child Wedding Cards - UN Women (Impact BBDO, Dubai).jpeg",
        "actual_tier": "Shortlist",
        "campaign": "Child Wedding Cards",
        "agency": "Impact BBDO Dubai",
        "client": "UN Women",
        "client_international": True,
        "exclude_ids": None,
    },
    {
        "label": "[Shortlist] Anywhere Any Way - DHL",
        "image_path": ROOT / "2024" / "PRINT&PUBLISHING" / "SHORTLIST" / "Anywhere, Any Way - DHL (Horizon FCB, Dubai).jpeg",
        "actual_tier": "Shortlist",
        "campaign": "Anywhere, Any Way",
        "agency": "Horizon FCB Dubai",
        "client": "DHL",
        "client_international": True,
        "exclude_ids": None,
    },
]


TIER_RANK: dict[str, int] = {
    "Grand Prix": 5, "Gold": 4, "Silver": 3, "Bronze": 2,
    "Shortlist": 1, "Loser": 0, "No Medal": 0,
}


def main() -> None:
    OUT_PATH.parent.mkdir(exist_ok=True)
    missing = [c["image_path"] for c in TEST_SET if not c["image_path"].exists()]
    if missing:
        print("⚠️  Missing files:")
        for p in missing:
            print(f"  - {p}")
        raise SystemExit(1)

    results: list[dict] = []
    t_total = perf_counter()
    for i, case in enumerate(TEST_SET, start=1):
        path: Path = case["image_path"]
        print(f"\n{'=' * 70}")
        print(f"[{i}/{len(TEST_SET)}] {case['label']}")
        print(f"  actual_tier : {case['actual_tier']}")

        metadata = UserMetadata(
            campaign_name=case["campaign"],
            agency=case["agency"],
            client=case["client"],
            category="Print & Publishing",
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
                "malus_multiplier": evaluation.malus["multiplier"],
                "exclude_ids": list(case["exclude_ids"]) if case.get("exclude_ids") else None,
            }
            tier_rank_actual = TIER_RANK.get(case["actual_tier"], -1)
            tier_rank_pred = TIER_RANK.get(evaluation.predicted_tier, -1)
            record["tier_distance"] = abs(tier_rank_actual - tier_rank_pred)
            results.append(record)

            print(f"  → predicted : {evaluation.predicted_tier} ({tp.score_percent}%, {tp.confidence})")
            print(f"  → axes      : I={record['axis_scores']['idea']}  S={record['axis_scores']['strategy']}  "
                  f"E={record['axis_scores']['execution']}  R={record['axis_scores']['impact']}")
            print(f"  → distance  : {record['tier_distance']}")
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            results.append({"label": case["label"], "actual_tier": case["actual_tier"], "error": str(e)})

    with OUT_PATH.open("w") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    elapsed = perf_counter() - t_total
    print(f"\n{'=' * 70}")
    print(f"✅ Calibration done in {elapsed:.1f}s — {len(results)} results saved to {OUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
