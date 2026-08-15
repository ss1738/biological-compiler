"""
Folds shortlisted candidate sequences with Chai-1, a second, architecturally
independent structure-prediction model (AlphaFold3-class diffusion model, not a
language-model-based folder like ESMFold), as a fourth check alongside ESMFold
self-consistency, OpenMM MD relaxation, and DiffDock docking.

Setup:
    python3 -m venv chai_venv
    chai_venv/bin/pip install torch==2.11.0+cu128 torchvision==0.26.0+cu128 \
        --index-url https://download.pytorch.org/whl/cu128
    chai_venv/bin/pip install chai_lab==0.6.1

IMPORTANT: installing chai_lab will silently downgrade torch to a version it
declares support for (as of writing, <2.7), which does NOT work on Blackwell
GPUs (confirmed: "CUDA error: no kernel image is available for execution on
the device"). Fix by force-reinstalling the correct torch version afterward:

    chai_venv/bin/pip install torch==2.11.0+cu128 torchvision==0.26.0+cu128 \
        --index-url https://download.pytorch.org/whl/cu128 --force-reinstall

(NOT --no-deps -- that leaves mismatched CUDA library versions behind and
breaks torch's import entirely with an undefined-symbol error. Let pip pull
the matching nvidia-* packages too.)

Then verify both GPU compute AND chai_lab import actually work together before
trusting the install -- the empirically-confirmed torch version here is well
past what chai_lab's metadata claims to support, worth re-checking if it's
ever updated.

Usage:
    python chai1_fold.py --manifest ../data/shortlist/manifest.csv \
        --out-dir ./chai1_results --chai-bin ~/chai_venv/bin/chai-lab
"""
import argparse
import csv
import json
import os
import subprocess
import time

import numpy as np


def write_fasta(gid, sequence, path):
    with open(path, "w") as f:
        f.write(f">protein|name={gid}\n{sequence}\n")


def fold_one(chai_bin, fasta_path, out_dir):
    result = subprocess.run([chai_bin, "fold", fasta_path, out_dir], capture_output=True, text=True)
    if result.returncode != 0:
        return None, result.stderr
    scores = np.load(f"{out_dir}/scores.model_idx_0.npz")
    # pTM, not the CLI's printed "Score"/aggregate_score -- see research/chai1_results.md
    # for why those are a different, less interpretable composite metric.
    return float(scores["ptm"][0]), None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", required=True, help="shortlist manifest.csv")
    p.add_argument("--out-dir", required=True)
    p.add_argument("--chai-bin", required=True)
    args = p.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    rows = list(csv.DictReader(open(args.manifest)))
    print(f"{len(rows)} candidates to fold", flush=True)

    results = []
    for i, row in enumerate(rows, 1):
        gid = row["global_id"]
        fasta_path = f"{args.out_dir}/{gid}.fasta"
        write_fasta(gid, row["sequence"], fasta_path)
        candidate_out = f"{args.out_dir}/{gid}"

        t0 = time.time()
        ptm, err = fold_one(args.chai_bin, fasta_path, candidate_out)
        elapsed = time.time() - t0
        if err:
            print(f"[{i}/{len(rows)}] {gid}: FAILED: {err[-500:]}", flush=True)
            results.append(dict(gid=gid, ok=False))
            continue
        results.append(dict(gid=gid, ok=True, ptm=ptm, elapsed=elapsed))
        print(f"[{i}/{len(rows)}] {gid}: ptm={ptm:.3f} ({elapsed:.1f}s)", flush=True)

    with open(f"{args.out_dir}/chai_summary.json", "w") as f:
        json.dump(results, f, indent=2)

    ok = [r for r in results if r["ok"]]
    ptms = [r["ptm"] for r in ok]
    print(f"\n=== SUMMARY: {len(ok)}/{len(results)} succeeded ===")
    if ptms:
        print(f"pTM: mean={sum(ptms)/len(ptms):.3f} min={min(ptms):.3f} max={max(ptms):.3f}")
        print(f"n with pTM > 0.5 (confident): {sum(1 for p in ptms if p > 0.5)}/{len(ptms)}")
        print(f"n with pTM > 0.7 (high): {sum(1 for p in ptms if p > 0.7)}/{len(ptms)}")

    os._exit(0)  # same torch/CUDA context teardown hang observed elsewhere in this project


if __name__ == "__main__":
    main()
