"""
Turns the raw per-sequence results.jsonl log(s) from pipeline.py into a small,
diverse shortlist — the actual script (a machine-specific one-off version of this)
that produced data/shortlist/ from 3,600 raw sequences across two campaign runs.

Diversity matters here: sorting by RMSD alone tends to let a handful of lucky
backbones dominate the top of the list. Capping candidates-per-backbone spreads
the shortlist across more distinct designs instead of returning near-duplicates.

Usage:
    python curate_shortlist.py results1.jsonl results2.jsonl --out-dir ./shortlist
"""
import argparse
import json
import os
import csv
import shutil


def curate(jsonl_paths, out_dir, n=30, max_per_backbone=3, plddt_thresh=65.0, rmsd_thresh=2.0):
    os.makedirs(f"{out_dir}/pdbs", exist_ok=True)

    recs = []
    for path in jsonl_paths:
        # results.jsonl is named identically across every pipeline.py run (it's always
        # "results.jsonl" inside <out-dir>/logs/), so the batch label has to come from
        # the run's own output directory name, not the log file's basename.
        batch = os.path.basename(os.path.dirname(os.path.dirname(os.path.abspath(path))))
        for line in open(path):
            r = json.loads(line)
            r["batch"] = batch
            r["global_id"] = f"{batch}_{r['backbone']}_seq{r['seq_idx']}"
            recs.append(r)

    passed = [r for r in recs if r["mean_plddt"] >= plddt_thresh and r["active_site_rmsd"] <= rmsd_thresh]
    passed.sort(key=lambda r: (r["active_site_rmsd"], -r["mean_plddt"]))

    selected = []
    per_backbone_count = {}
    for r in passed:
        key = (r["batch"], r["backbone"])
        if per_backbone_count.get(key, 0) >= max_per_backbone:
            continue
        selected.append(r)
        per_backbone_count[key] = per_backbone_count.get(key, 0) + 1
        if len(selected) >= n:
            break

    print(f"Total passed pool: {len(passed)}")
    print(f"Selected: {len(selected)} from {len(per_backbone_count)} distinct backbones (max {max_per_backbone}/backbone)")

    with open(f"{out_dir}/manifest.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["rank", "global_id", "batch", "backbone", "seq_idx", "mean_plddt",
                    "active_site_rmsd", "seq_length", "sequence"])
        for i, r in enumerate(selected, 1):
            w.writerow([i, r["global_id"], r["batch"], r["backbone"], r["seq_idx"],
                        f"{r['mean_plddt']:.1f}", f"{r['active_site_rmsd']:.2f}",
                        len(r["seq"]), r["seq"]])

    with open(f"{out_dir}/shortlist.fasta", "w") as f:
        for i, r in enumerate(selected, 1):
            f.write(f">rank{i:02d}_{r['global_id']} pLDDT={r['mean_plddt']:.1f} "
                    f"active_site_RMSD={r['active_site_rmsd']:.2f}A\n")
            f.write(r["seq"] + "\n")

    for i, r in enumerate(selected, 1):
        dst = f"{out_dir}/pdbs/rank{i:02d}_{r['global_id']}.pdb"
        if os.path.exists(r["fold_pdb"]):
            shutil.copy(r["fold_pdb"], dst)
        else:
            print(f"  WARNING: missing source pdb for {r['global_id']}: {r['fold_pdb']}")

    return selected


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("jsonl_paths", nargs="+")
    p.add_argument("--out-dir", required=True)
    p.add_argument("-n", type=int, default=30)
    p.add_argument("--max-per-backbone", type=int, default=3)
    args = p.parse_args()
    curate(args.jsonl_paths, args.out_dir, n=args.n, max_per_backbone=args.max_per_backbone)
