"""Phase 3 — Calibration test for PR.

Evaluate the full pipeline (extract → RAG → judge → malus → tier) on a
diverse PR test set, then compare predicted vs actual tier.

Test set (10 boards):
    A. Hold-out winners (7)        → exclude_ids self-match to simulate unseen
       (1 Grand Prix + 2 Gold + 2 Silver + 2 Bronze)
    B. Shortlists (3)              → genuinely unseen by the system (no exclude_ids needed)

Cost: ~$15-20 (10 × ~$1.50). Runtime: ~8 min sequential.
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
    # ---- A. HOLD-OUT WINNERS (in index, exclude self-id to simulate unseen) ----
    {
        "label": "[Hold-out GP] The Misheard Version - Specsavers",
        "image_path": ROOT / "2024" / "PR" / "GRAND PRIX" / "The Misheard Version - Specsavers (Golin London).jpg",
        "actual_tier": "Grand Prix",
        "campaign": "The Misheard Version",
        "agency": "Golin London",
        "client": "Specsavers",
        "client_international": False,  # UK/Ireland chain
        "exclude_ids": {"the-misheard-version-specsavers-golin-london"},
    },
    {
        "label": "[Hold-out Gold] Bar Experience - Heineken",
        "image_path": ROOT / "2024" / "PR" / "GOLD" / "Bar Experience - Heineken (LePub Milan).jpg",
        "actual_tier": "Gold",
        "campaign": "Bar Experience",
        "agency": "LePub Milan",
        "client": "Heineken",
        "client_international": True,
        "exclude_ids": {"bar-experience-heineken-lepub-milan"},
    },
    {
        "label": "[Hold-out Gold] In Transit - Callen-Lorde",
        "image_path": ROOT / "2024" / "PR" / "GOLD" / "In Transit, Callen-Lorde, Metropolitan Transportation Authority, NYC LGBT Historic Sites Pro (AREA 23, New York).jpeg",
        "actual_tier": "Gold",
        "campaign": "In Transit",
        "agency": "AREA 23 New York",
        "client": "Callen-Lorde",
        "client_international": False,  # NYC clinic
        "exclude_ids": {"in-transit-callen-lorde-metropolitan-transportation-authority-nyc-lgbt-historic-"},
    },
    {
        "label": "[Hold-out Silver] A True Story - Gustave Roussy",
        "image_path": ROOT / "2024" / "PR" / "SILVER" / "A True Story - Gustave Roussy (Publicis Conseil, Paris).webp",
        "actual_tier": "Silver",
        "campaign": "A True Story",
        "agency": "Publicis Conseil Paris",
        "client": "Gustave Roussy",
        "client_international": False,  # French cancer hospital
        "exclude_ids": {"a-true-story-gustave-roussy-publicis-conseil-paris"},
    },
    {
        "label": "[Hold-out Silver] Code My Crown - Dove",
        "image_path": ROOT / "2024" / "PR" / "SILVER" / "Code My Crown - Dove (Edelman, London).webp",
        "actual_tier": "Silver",
        "campaign": "Code My Crown",
        "agency": "Edelman London",
        "client": "Dove",
        "client_international": True,
        "exclude_ids": {"code-my-crown-dove-edelman-london"},
    },
    {
        "label": "[Hold-out Bronze] Call Glenn - Child Focus",
        "image_path": ROOT / "2024" / "PR" / "BRONZE" / "Call Glenn - Child Focus (VML Belgium, Antwerp _ Wunderman Thompson, Antwerp).jpeg",
        "actual_tier": "Bronze",
        "campaign": "Call Glenn",
        "agency": "VML Belgium Antwerp",
        "client": "Child Focus",
        "client_international": False,  # Belgian NGO
        "exclude_ids": {"call-glenn-child-focus-vml-belgium-antwerp-wunderman-thompson-antwerp"},
    },
    {
        "label": "[Hold-out Bronze] Freeing Taco T-Day - Taco Bell",
        "image_path": ROOT / "2024" / "PR" / "BRONZE" / "Freeing Taco T_Day - Taco Bell (Deutsch Los Angeles).webp",
        "actual_tier": "Bronze",
        "campaign": "Freeing Taco Tuesday",
        "agency": "Deutsch Los Angeles",
        "client": "Taco Bell",
        "client_international": True,
        "exclude_ids": {"freeing-taco-t-day-taco-bell-deutsch-los-angeles"},
    },
    # ---- B. SHORTLISTS (not in index, truly held-out) ----
    {
        "label": "[Shortlist] I Care - Royal Commission for AlUla",
        "image_path": ROOT / "2024" / "PR" / "SHORTLIST" / "I Care - Royal Commission For Alula (Hill+KnowltonL Strategies, Dubai).jpg",
        "actual_tier": "Shortlist",
        "campaign": "I Care",
        "agency": "Hill+Knowlton Strategies Dubai",
        "client": "Royal Commission for AlUla",
        "client_international": False,  # Saudi tourism authority
        "exclude_ids": None,
    },
    {
        "label": "[Shortlist] Supercube - Knorr",
        "image_path": ROOT / "2024" / "PR" / "SHORTLIST" / "Supercube - Knorr (Weber Shandwick, Cologne).webp",
        "actual_tier": "Shortlist",
        "campaign": "Supercube",
        "agency": "Weber Shandwick Cologne",
        "client": "Knorr",
        "client_international": True,
        "exclude_ids": None,
    },
    {
        "label": "[Shortlist] The Hippocratic Oath 2023 - ISNI",
        "image_path": ROOT / "2024" / "PR" / "SHORTLIST" / "The Hippocratic Oath 2023 - Isni (Ogilvy Paris).webp",
        "actual_tier": "Shortlist",
        "campaign": "The Hippocratic Oath 2023",
        "agency": "Ogilvy Paris",
        "client": "ISNI",
        "client_international": False,  # French interns union
        "exclude_ids": None,
    },
]


# Mapping for confusion-matrix distance computation
TIER_RANK: dict[str, int] = {
    "Grand Prix": 5,
    "Gold": 4,
    "Silver": 3,
    "Bronze": 2,
    "Shortlist": 1,
    "Loser": 0,
    "No Medal": 0,
}


def main() -> None:
    OUT_PATH.parent.mkdir(exist_ok=True)
    results: list[dict] = []
    t_total = perf_counter()

    # Sanity check: all image paths must exist before we start
    missing = [c["image_path"] for c in TEST_SET if not c["image_path"].exists()]
    if missing:
        print("⚠️  Missing files:")
        for p in missing:
            print(f"  - {p}")
        raise SystemExit(1)

    for i, case in enumerate(TEST_SET, start=1):
        path: Path = case["image_path"]
        print(f"\n{'=' * 70}")
        print(f"[{i}/{len(TEST_SET)}] {case['label']}")
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
            results.append(record)

            print(f"  → predicted : {evaluation.predicted_tier} ({tp.score_percent}%, {tp.confidence})")
            print(f"  → axes      : I={record['axis_scores']['idea']}  S={record['axis_scores']['strategy']}  "
                  f"E={record['axis_scores']['execution']}  R={record['axis_scores']['impact']}")
            print(f"  → distance  : {record['tier_distance']}")
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            results.append({
                "label": case["label"],
                "actual_tier": case["actual_tier"],
                "error": str(e),
            })

    # Write results
    with OUT_PATH.open("w") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    elapsed = perf_counter() - t_total
    print(f"\n{'=' * 70}")
    print(f"✅ Calibration done in {elapsed:.1f}s — {len(results)} results saved to {OUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
