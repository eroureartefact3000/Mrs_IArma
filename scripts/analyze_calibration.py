"""Analyse the calibration results — rigorous metrics focused on the
PRIMARY user target: binary medal vs no-medal accuracy.

Metrics computed:
  1. **Binary accuracy** (medal vs no-medal) — primary target (85%+)
  2. **Threshold sweep**: scan P(medal) >= t for t in 0.30..0.70 to find optimal
  3. Within ±1 tier accuracy (debug only — argmax tier prediction)
  4. Probability calibration (Brier score, log-loss)
  5. Synthesis + tips quality check (length, plausibility)
"""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RESULTS_PATH = ROOT / "data_internal" / "calibration_results.jsonl"

TIER_RANK = {"Grand Prix": 5, "Gold": 4, "Silver": 3, "Bronze": 2, "Shortlist": 1, "Loser": 0, "No Medal": 0}
MEDAL_TIERS = {"Grand Prix", "Gold", "Silver", "Bronze"}
NON_MEDAL = {"Shortlist", "Loser"}  # map both to "No Medal" for binary comparison

# Map our actual-tier labels (Shortlist, Loser) to the "No Medal" probability bucket
ACTUAL_TO_BUCKET = {
    "Grand Prix": "Grand Prix",
    "Gold": "Gold",
    "Silver": "Silver",
    "Bronze": "Bronze",
    "Shortlist": "No Medal",
    "Loser": "No Medal",
}


def is_medal(tier: str) -> bool:
    return tier in MEDAL_TIERS


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS_PATH)
    args = parser.parse_args()
    results_path: Path = args.results

    records = [json.loads(line) for line in results_path.open() if line.strip()]
    records = [r for r in records if not r.get("error")]
    n = len(records)
    print(f"Analysing {n} records from {results_path.name}\n")

    # 1) Binary accuracy (medal / no-medal)
    binary_correct = sum(1 for r in records if is_medal(r["predicted_tier"]) == is_medal(r["actual_tier"]))

    # 2) Within ±1 tier (using argmax prediction)
    within_1 = 0
    exact = 0
    for r in records:
        rank_p = TIER_RANK.get(r["predicted_tier"], -1)
        rank_a = TIER_RANK.get(r["actual_tier"], -1)
        if rank_p == rank_a:
            exact += 1
        if abs(rank_p - rank_a) <= 1:
            within_1 += 1

    # 3) Probability calibration — Brier score (lower = better)
    # Multiclass Brier: sum over classes of (p_class - y_class)^2 where y_class is 0/1
    brier_scores: list[float] = []
    log_losses: list[float] = []
    p_actual: list[float] = []  # P(actual tier) per record
    p_no_medal_when_no_medal: list[float] = []  # P(No Medal) when actual is non-medal
    p_no_medal_when_medal: list[float] = []     # P(No Medal) when actual IS medal
    for r in records:
        probs = r.get("tier_probabilities") or {}
        if not probs:
            continue
        bucket = ACTUAL_TO_BUCKET[r["actual_tier"]]
        # Brier (multiclass)
        brier = 0.0
        for tier in ["Grand Prix", "Gold", "Silver", "Bronze", "No Medal"]:
            y = 1.0 if tier == bucket else 0.0
            p = probs.get(tier, 0.0)
            brier += (p - y) ** 2
        brier_scores.append(brier)
        # log-loss
        import math
        p_correct = max(probs.get(bucket, 0.0), 1e-9)
        log_losses.append(-math.log(p_correct))
        p_actual.append(probs.get(bucket, 0.0))
        if is_medal(r["actual_tier"]):
            p_no_medal_when_medal.append(probs.get("No Medal", 0.0))
        else:
            p_no_medal_when_no_medal.append(probs.get("No Medal", 0.0))

    # 4) Threshold sweep on P(medal) — the primary user-facing decision
    #    Predict medal if P(medal) >= t, where P(medal) = 1 - P(No Medal)
    best_thresh = None
    best_thresh_accuracy = 0.0
    threshold_table: list[tuple[float, int, int, int]] = []  # (thresh, correct, fp, fn)
    for thresh_pct in range(20, 75, 5):
        thresh = thresh_pct / 100
        correct = fp = fn = 0
        for r in records:
            probs = r.get("tier_probabilities") or {}
            if not probs:
                continue
            p_medal = 1.0 - probs.get("No Medal", 0.0)
            pred_medal = p_medal >= thresh
            actual_medal = is_medal(r["actual_tier"])
            if pred_medal == actual_medal:
                correct += 1
            elif pred_medal and not actual_medal:
                fp += 1
            elif not pred_medal and actual_medal:
                fn += 1
        threshold_table.append((thresh, correct, fp, fn))
        if correct > best_thresh_accuracy * n:
            best_thresh_accuracy = correct / n
            best_thresh = thresh

    print("=" * 72)
    print("ACCURACY METRICS")
    print("=" * 72)
    print(f"\nBinary (medal vs no medal)       : {binary_correct}/{n} = {100*binary_correct/n:.0f}%   [target: 85%+]")
    print(f"Exact tier match (argmax)        : {exact}/{n} = {100*exact/n:.0f}%")
    print(f"Within ±1 tier (argmax)          : {within_1}/{n} = {100*within_1/n:.0f}%   [target: 80%+]")

    if brier_scores:
        print(f"\nMean Brier score (lower=better)  : {statistics.mean(brier_scores):.3f}")
        print(f"Mean log-loss (lower=better)     : {statistics.mean(log_losses):.3f}")
        print(f"Mean P(actual tier)              : {statistics.mean(p_actual):.2f}  (how confident on correct answer)")

    if p_no_medal_when_no_medal and p_no_medal_when_medal:
        print(f"\nP(No Medal) when actual=no medal : {statistics.mean(p_no_medal_when_no_medal):.2f}  (should be HIGH)")
        print(f"P(No Medal) when actual=medal    : {statistics.mean(p_no_medal_when_medal):.2f}  (should be LOW)")
        diff = statistics.mean(p_no_medal_when_no_medal) - statistics.mean(p_no_medal_when_medal)
        print(f"Gap (higher = better separation) : {diff:+.2f}")

    if best_thresh is not None:
        print(f"\nBest medal threshold: P(medal) >= {best_thresh:.2f}  →  binary accuracy = {100*best_thresh_accuracy:.0f}%")
        print("\nFull threshold sweep (P(medal) >= t → MEDAL):")
        print(f"  {'t':<6s} {'correct':<8s} {'fp':<4s} {'fn':<4s} {'acc':<6s}")
        for thresh, correct, fp, fn in threshold_table:
            star = " ★" if thresh == best_thresh else ""
            print(f"  {thresh:<6.2f} {correct}/{n:<6d} {fp:<4d} {fn:<4d} {100*correct/n:<5.0f}%{star}")

    print("\n" + "=" * 72)
    print("PER-RECORD DETAIL")
    print("=" * 72)
    print(f"\n{'CASE':<48s} {'ACT':<10s} {'PRED':<10s} {'BIN':<4s} {'P(actual)':<10s} {'P(NoMedal)':<10s}")
    print("-" * 100)
    for r in records:
        bucket = ACTUAL_TO_BUCKET[r["actual_tier"]]
        probs = r.get("tier_probabilities") or {}
        p_act = probs.get(bucket, float('nan'))
        p_nm = probs.get("No Medal", float('nan'))
        binary = "✓" if is_medal(r["predicted_tier"]) == is_medal(r["actual_tier"]) else "✗"
        p_act_str = f"{p_act:.2f}" if not (p_act != p_act) else "n/a"
        p_nm_str = f"{p_nm:.2f}" if not (p_nm != p_nm) else "n/a"
        print(f"{r['label']:<48s} {r['actual_tier']:<10s} {r['predicted_tier']:<10s} {binary:<4s} {p_act_str:<10s} {p_nm_str:<10s}")

    # Show full probability distributions
    print("\n" + "=" * 72)
    print("FULL PROBABILITY DISTRIBUTIONS")
    print("=" * 72)
    for r in records:
        probs = r.get("tier_probabilities") or {}
        if not probs:
            continue
        line = f"\n[{r['actual_tier']:<10s}] {r['label']}"
        print(line)
        for tier in ["Grand Prix", "Gold", "Silver", "Bronze", "No Medal"]:
            p = probs.get(tier, 0.0)
            bar = "█" * int(round(p * 30))
            mark = " ←" if ACTUAL_TO_BUCKET[r["actual_tier"]] == tier else ""
            print(f"     {tier:12s} {p:5.1%}  {bar}{mark}")


if __name__ == "__main__":
    main()
