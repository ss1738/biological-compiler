"""
Extracts top-pose confidence scores from a DiffDock output directory (one
subdirectory per complex, named `<candidate>__<substrate>`) and summarizes by
substrate. This is the actual script that produced
data/shortlist/diffdock_summary.json and research/diffdock_results.md's numbers.

Usage:
    python summarize_diffdock.py --results-dir ../data/shortlist/diffdock_results \
        --out summary.json
"""
import argparse
import glob
import json
import os
import re
import statistics


def summarize(results_dir):
    results = []
    for d in sorted(os.listdir(results_dir)):
        files = glob.glob(f"{results_dir}/{d}/rank1_confidence*.sdf")
        if not files:
            results.append(dict(complex=d, top_confidence=None))
            continue
        m = re.search(r"confidence(-?[\d.]+)\.sdf", files[0])
        results.append(dict(complex=d, top_confidence=float(m.group(1)) if m else None))
    return results


def print_summary(results):
    valid = [r for r in results if r["top_confidence"] is not None]
    print(f"n={len(results)} total, {len(valid)} with valid top pose")

    by_substrate = {}
    for r in valid:
        sub = r["complex"].split("__")[-1]
        by_substrate.setdefault(sub, []).append(r["top_confidence"])

    for sub, vals in by_substrate.items():
        high = sum(1 for v in vals if v > 0)
        moderate = sum(1 for v in vals if -1.5 < v <= 0)
        print(f"{sub}: n={len(vals)} mean={statistics.mean(vals):.2f} min={min(vals):.2f} max={max(vals):.2f} "
              f"high_confidence(c>0)={high}/{len(vals)} moderate(-1.5<c<=0)={moderate}/{len(vals)}")

    print("\ntop 5 overall:")
    for r in sorted(valid, key=lambda r: -r["top_confidence"])[:5]:
        print(f"  {r['complex']}: {r['top_confidence']:.2f}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--results-dir", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    results = summarize(args.results_dir)
    with open(args.out, "w") as f:
        json.dump(results, f, indent=2)
    print_summary(results)
