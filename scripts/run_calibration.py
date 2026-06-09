"""Phase 3 — Calibration test.

Evaluate the full pipeline (extract → RAG → judge → malus → tier) on a
diverse test set, then compare predicted vs actual tier.

Test set (10 boards):
    A. Losers in index (2)         → exclude_ids self-match
    B. Hold-out 2024 winners (5)   → exclude_ids to simulate unseen
    C. Fresh 2025 Outdoor (3)      → genuinely unseen by the system

Cost: ~$19 (10 × $1.90). Runtime: ~8 min sequential.
"""
from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter

from pipeline.evaluate import evaluate_board
from pipeline.schema import UserMetadata

ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT / "data_internal" / "calibration_results.jsonl"


# Each entry: dict with image_path, actual_tier, metadata, exclude_ids
TEST_SET: list[dict] = [
    # ---- A. LOSERS (already in index) ----
    {
        "label": "[Loser] KitKat Break Chair",
        "image_path": ROOT / "2024" / "loser" / "The KitKat Break Chair - VML Sydney.avif",
        "actual_tier": "Loser",
        "agency": "VML Sydney",
        "client": "KitKat",
        "client_international": True,
        "exclude_ids": {"the-kitkat-break-chair-vml-sydney"},
    },
    {
        "label": "[Loser] IKEA Supporting First Steps",
        "image_path": ROOT / "2024" / "loser" / "Supporting First Steps - IKEA - INGO Hamburg.png",
        "actual_tier": "Loser",
        "agency": "INGO Hamburg",
        "client": "IKEA",
        "client_international": True,
        "exclude_ids": {"supporting-first-steps-ikea-ingo-hamburg"},
    },
    # ---- B. HOLD-OUT 2024 WINNERS (in index, exclude_ids to simulate unseen) ----
    {
        "label": "[Hold-out GP] Adoptable - Pedigree",
        "image_path": ROOT / "2024" / "OUTDOOR" / "GRAND PRIX" / "Adoptable - Pedigree (Colenso BBDO, Auckland).webp",
        "actual_tier": "Grand Prix",
        "agency": "Colenso BBDO Auckland",
        "client": "Pedigree",
        "client_international": True,
        "exclude_ids": {"adoptable-pedigree-colenso-bbdo-auckland"},
    },
    {
        "label": "[Hold-out Gold] Clean Sponsorship - Consul",
        "image_path": ROOT / "2024" / "OUTDOOR" / "GOLD" / "Clean Sponsorship - Consul (DM9, Sao Paulo).jpeg",
        "actual_tier": "Gold",
        "agency": "DM9 Sao Paulo",
        "client": "Consul",
        "client_international": True,
        "exclude_ids": {"clean-sponsorship-consul-dm9-sao-paulo"},
    },
    {
        "label": "[Hold-out Silver] 855-HOW-TO-QUIT - Anzen Health",
        "image_path": ROOT / "2024" / "OUTDOOR" / "SILVER" / "855-How-To-Quit-(Opioids) - Anzen Health (Serviceplan Munich).jpeg",
        "actual_tier": "Silver",
        "agency": "Serviceplan Munich",
        "client": "Anzen Health",
        "client_international": True,
        "exclude_ids": {"855-how-to-quit-opioids-anzen-health-serviceplan-munich"},
    },
    {
        "label": "[Hold-out Bronze] Et le Buuuuud - Budweiser",
        "image_path": ROOT / "2024" / "OUTDOOR" / "BRONZE" / "Et Le Buuuuud - Budweiser (BETC Paris).webp",
        "actual_tier": "Bronze",
        "agency": "BETC Paris",
        "client": "Budweiser",
        "client_international": True,
        "exclude_ids": {"et-le-buuuuud-budweiser-betc-paris"},
    },
    {
        "label": "[Hold-out Shortlist] A British Original - British Airways",
        "image_path": ROOT / "2024" / "OUTDOOR" / "SHORTLIST" / "A British Original - British Airways (Uncommon, London).jpeg",
        "actual_tier": "Shortlist",
        "agency": "Uncommon London",
        "client": "British Airways",
        "client_international": True,
        "exclude_ids": {"a-british-original-british-airways-uncommon-london"},
    },
    # ---- C. FRESH 2025 BOARDS (truly unseen by the index) ----
    {
        "label": "[2025 GP] Paris 2024 Opening Ceremony",
        "image_path": ROOT / "2025" / "Grand Prix" / "Cannes-Lions-2025-Outdoor-Grand-Prix-Paris-2024-Opening-Ceremony-by-Paname-24-Auditoire-Double-2-Havas-Paris-Havas-Events-Obo-Paris.jpg",
        "actual_tier": "Grand Prix",
        "agency": "Havas Paris",
        "client": "Paris 2024",
        "client_international": True,
        "exclude_ids": None,
    },
    {
        "label": "[2025 Gold] Heinz It Has To Be",
        "image_path": ROOT / "2025" / "Gold" / "It has to be - Heinz - W+K London.avif",
        "actual_tier": "Gold",
        "agency": "Wieden+Kennedy London",
        "client": "Heinz",
        "client_international": True,
        "exclude_ids": None,
    },
    {
        "label": "[2025 Silver] Bundles of Joy - Burger King",
        "image_path": ROOT / "2025" / "Silver" / "BUNDLES OF JOY – BURGER KING (BBH LONDON).avif",
        "actual_tier": "Silver",
        "agency": "BBH London",
        "client": "Burger King",
        "client_international": True,
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

    for i, case in enumerate(TEST_SET, start=1):
        path: Path = case["image_path"]
        print(f"\n{'=' * 70}")
        print(f"[{i}/{len(TEST_SET)}] {case['label']}")
        print(f"  file : {path.relative_to(ROOT)}")
        print(f"  actual_tier : {case['actual_tier']}")

        if not path.exists():
            print(f"  ⚠️  FILE NOT FOUND — skipping")
            continue

        metadata = UserMetadata(
            campaign_name=case["label"],
            agency=case["agency"],
            client=case["client"],
            category="Outdoor",
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
            record = {
                "label": case["label"],
                "image_path": str(path.relative_to(ROOT)),
                "actual_tier": case["actual_tier"],
                "agency": case["agency"],
                "client": case["client"],
                "predicted_tier": evaluation.predicted_tier,
                "tier_probabilities": evaluation.tier_probabilities,
                "medal_probability": evaluation.medal_prediction.medal_probability,
                "will_medal_predicted": evaluation.medal_prediction.will_medal,
                "confidence": evaluation.medal_prediction.confidence,
                "synthesis": evaluation.medal_prediction.synthesis,
                "base_score": evaluation.base_weighted_score,
                "final_score": evaluation.final_weighted_score,
                "malus_multiplier": evaluation.malus["multiplier"],
                "malus_applied": [
                    n for n, applied in [
                        ("aesthetic", evaluation.malus["aesthetic_applied"]),
                        ("client", evaluation.malus["client_applied"]),
                        ("network", evaluation.malus["network_applied"]),
                    ] if applied
                ],
                "detected_holding": evaluation.malus.get("detected_holding"),
                "verdict": evaluation.analysis.why_it_won.verdict,
                "references": [
                    {"id": r.id, "tier": r.tier, "similarity": r.similarity_score}
                    for r in evaluation.references
                ],
                "pass_scores": evaluation.pass_scores,
                "pass_probs": evaluation.pass_probs,
            }
            results.append(record)

            print(
                f"  PREDICTED   : {evaluation.predicted_tier}  "
                f"(base={evaluation.base_weighted_score:.1f}, mult={evaluation.malus['multiplier']:.2f}, final={evaluation.final_weighted_score:.1f})"
            )
            actual_rank = TIER_RANK.get(case["actual_tier"], -1)
            predicted_rank = TIER_RANK.get(evaluation.predicted_tier, -1)
            diff = predicted_rank - actual_rank
            tag = "✅ MATCH" if diff == 0 else f"⚠️  Δ={diff:+d} tier(s)"
            print(f"  {tag}")

        except Exception as e:  # noqa: BLE001
            print(f"  ❌ ERROR: {type(e).__name__}: {e}")
            results.append({
                "label": case["label"],
                "actual_tier": case["actual_tier"],
                "error": f"{type(e).__name__}: {e}",
            })

    # Save all
    with OUT_PATH.open("w") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    elapsed = perf_counter() - t_total
    print(f"\n{'=' * 70}")
    print(f"Total : {elapsed:.0f}s  ·  saved to {OUT_PATH.relative_to(ROOT)}")

    # Confusion summary
    print("\n=== Confusion matrix ===\n")
    print(f"{'CASE':<48s} {'ACTUAL':<12s} {'PREDICTED':<12s} {'Δ':<4s}  {'MALUS'}")
    print("-" * 100)
    total_correct = 0
    total_within_1 = 0
    total_evaluated = 0
    malus_dominant_misses = 0
    for r in results:
        if r.get("error"):
            continue
        total_evaluated += 1
        actual_rank = TIER_RANK.get(r["actual_tier"], -1)
        predicted_rank = TIER_RANK.get(r["predicted_tier"], -1)
        diff = predicted_rank - actual_rank
        if diff == 0:
            total_correct += 1
        if abs(diff) <= 1:
            total_within_1 += 1
        # malus-dominant: if without malus the prediction would have been correct
        # (heuristic: if final < base and base would have predicted ≥ actual_rank)
        if diff < 0 and r["malus_multiplier"] < 1.0:
            # what tier would the base score predict?
            from pipeline.evaluate import _score_to_tier
            base_tier = _score_to_tier(r["base_score"])
            if TIER_RANK.get(base_tier, -1) >= actual_rank:
                malus_dominant_misses += 1

        malus_str = ",".join(r.get("malus_applied", [])) or "-"
        print(
            f"{r['label']:<48s} {r['actual_tier']:<12s} {r['predicted_tier']:<12s} {diff:+d}    {malus_str}"
        )

    print("\n=== Accuracy ===")
    print(f"  Exact match     : {total_correct}/{total_evaluated}  ({100*total_correct/max(total_evaluated,1):.0f}%)")
    print(f"  Within ±1 tier  : {total_within_1}/{total_evaluated}  ({100*total_within_1/max(total_evaluated,1):.0f}%)")
    print(f"  Malus-dominated misses : {malus_dominant_misses}  (cases where removing malus would have brought the prediction back to or above actual)")


if __name__ == "__main__":
    main()
