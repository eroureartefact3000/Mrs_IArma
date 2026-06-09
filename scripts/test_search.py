"""Smoke test the Outdoor vector index.

Runs 7 diverse queries and prints the top-5 hits per query. Use this to confirm
the retrieval is conceptually relevant (similar mechanic / theme / format) and
not just keyword-matching.
"""
from pipeline.search import search

QUERIES = [
    # 1 — pure mechanic
    "object-as-medium ambient: an everyday product becomes the billboard",
    # 2 — purpose-led narrative
    "purpose-driven shelter and pet adoption campaign",
    # 3 — competitor ambush
    "competitor ambush wordplay or naming hack",
    # 4 — visual transformation
    "billboard that physically transforms with the environment (sun, rain, time of day)",
    # 5 — cultural prank
    "ambient prank that goes viral in public space",
    # 6 — sponsorship inversion
    "brand that paid to remove its own logo from media space",
    # 7 — out-of-distribution
    "a 100-word essay about quantum computing",
]


def main() -> None:
    for q in QUERIES:
        print(f"\n=== QUERY: {q} ===")
        results = search(q, k=5)
        if not results:
            print("  (no hits)")
            continue
        for r in results:
            tier = (r.get("tier") or "?")[:11]
            campaign = (r.get("campaign") or "?")[:32]
            one = (r.get("one_liner") or "")[:65]
            print(f"  {r['score']:.3f}  [{tier:11s}]  {campaign:<32s}  | {one}")


if __name__ == "__main__":
    main()
