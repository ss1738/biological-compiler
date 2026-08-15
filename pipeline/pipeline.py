"""
End-to-end orchestration: RFdiffusion -> ProteinMPNN -> ESMFold -> filter.

This is a refactored version of the actual script that produced every result in
data/shortlist/ (originally a single flat file, pfas_campaign.py; split up here
for readability). The logic is unchanged. Run on a machine with the
rfdiffusion-rtx5090:latest Docker image already built (see docker/) and an RTX
5090 or equivalent (32GB+ VRAM) — this was developed and tested on exactly that
hardware, nothing else.

Usage:
    python pipeline.py --n-backbones 100 --out-dir ./campaign
"""
import argparse
import json
import os
import subprocess
import time

import rfdiffusion_setup as rfd
import proteinmpnn_wrapper as mpnn
import esmfold_filter as esm
from compute_rmsd import active_site_rmsd


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--rfdiffusion-dir", default=os.path.expanduser("~/biocompiler/RFdiffusion"))
    p.add_argument("--models-dir", default=os.path.expanduser("~/biocompiler/RFdiffusion/models"))
    p.add_argument("--mpnn-dir", default=os.path.expanduser("~/biocompiler/ProteinMPNN"))
    p.add_argument("--py-bin", default=os.path.expanduser("~/biocompiler/venv/bin/python3"))
    p.add_argument("--out-dir", required=True)
    p.add_argument("--n-backbones", type=int, default=100)
    p.add_argument("--seqs-per-temp", type=int, default=3)
    args = p.parse_args()

    problems = rfd.validate_setup(args.rfdiffusion_dir, args.models_dir)
    if problems:
        for prob in problems:
            log(f"SETUP PROBLEM: {prob}")
        raise SystemExit(1)

    for d in ["rfdiffusion_outputs", "mpnn_work", "esmfold_outputs", "candidates", "logs"]:
        os.makedirs(f"{args.out_dir}/{d}", exist_ok=True)
    log_path = f"{args.out_dir}/logs/results.jsonl"
    log_f = open(log_path, "a")

    log("Loading ESMFold (facebook/esmfold_v1)...")
    t0 = time.time()
    tokenizer, model = esm.load_model()
    log(f"ESMFold loaded in {time.time()-t0:.1f}s")

    n_candidates = 0
    n_total_seqs = 0

    for i in range(1, args.n_backbones + 1):
        prefix = f"design_{i:04d}"
        log(f"=== Backbone {i}/{args.n_backbones} ({prefix}) ===")

        pdb_path, trb_path, result = rfd.generate_backbone(
            args.rfdiffusion_dir, args.models_dir,
            f"{args.out_dir}/rfdiffusion_outputs", prefix)
        if pdb_path is None:
            log(f"  RFdiffusion FAILED for {prefix}: {result.stderr[-500:]}")
            continue

        motif_positions = rfd.load_motif_positions(trb_path)
        log(f"  backbone generated, motif now at positions {motif_positions}")

        sequences = mpnn.design_sequences(
            args.mpnn_dir, args.py_bin, pdb_path, motif_positions,
            f"{args.out_dir}/mpnn_work", seqs_per_temp=args.seqs_per_temp, seed=i)
        log(f"  {len(sequences)} sequences generated")

        for j, (header, seq) in enumerate(sequences):
            n_total_seqs += 1
            mean_plddt, pdb_str = esm.fold(tokenizer, model, seq)
            fold_path = f"{args.out_dir}/esmfold_outputs/{prefix}_seq{j}.pdb"
            with open(fold_path, "w") as f:
                f.write(pdb_str)

            try:
                rmsd = active_site_rmsd(pdb_path, fold_path, motif_positions)
            except ValueError as e:
                log(f"    seq{j}: {e}, skipping")
                continue

            record = dict(backbone=prefix, seq_idx=j, header=header, seq=seq,
                           mean_plddt=mean_plddt, active_site_rmsd=rmsd["active_site_rmsd"],
                           backbone_rmsd=rmsd["backbone_rmsd"], motif_positions=motif_positions,
                           fold_pdb=fold_path, backbone_pdb=pdb_path)
            log_f.write(json.dumps(record) + "\n")
            log_f.flush()

            if esm.passes(mean_plddt, rmsd["active_site_rmsd"]):
                n_candidates += 1
                cand_name = (f"{args.out_dir}/candidates/cand{n_candidates:04d}_{prefix}_seq{j}"
                             f"_pLDDT{mean_plddt:.0f}_RMSD{rmsd['active_site_rmsd']:.2f}.pdb")
                subprocess.run(f"cp {fold_path} {cand_name}", shell=True)
                log(f"    seq{j}: pLDDT={mean_plddt:.1f} RMSD={rmsd['active_site_rmsd']:.2f}A  PASS -> candidate #{n_candidates}")
            else:
                log(f"    seq{j}: pLDDT={mean_plddt:.1f} RMSD={rmsd['active_site_rmsd']:.2f}A")

        log(f"  running totals: {n_total_seqs} sequences evaluated, {n_candidates} candidates passed")

    log(f"=== COMPLETE: {args.n_backbones} backbones, {n_total_seqs} sequences, {n_candidates} candidates ===")
    log_f.close()

    # torch/CUDA context teardown has hung on the machine this was developed on
    # (measured: processes stayed alive holding 14GB VRAM well after finishing).
    # Force-exit rather than trust normal interpreter shutdown.
    os._exit(0)


if __name__ == "__main__":
    main()
