"""
Builds the protein/ligand CSV DiffDock's inference.py expects, pairing every
relaxed candidate structure against a set of real substrates.

DiffDock's own environment.yml pins PyTorch 1.13.1 + CUDA 11.7 (2022-era), which
doesn't work on Blackwell hardware -- same class of problem RFdiffusion had.
Rebuild against a modern stack instead:

    python3 -m venv diffdock_venv
    diffdock_venv/bin/pip install torch==2.11.0+cu128 torchvision==0.26.0+cu128 \
        --index-url https://download.pytorch.org/whl/cu128
    diffdock_venv/bin/pip install torch-geometric torch-scatter torch-cluster torch-sparse \
        -f https://data.pyg.org/whl/torch-2.11.0+cu128.html
    diffdock_venv/bin/pip install e3nn rdkit fair-esm pyyaml networkx pandas scikit-learn \
        biopython prody spyrmsd

Then run inference.py from a checkout of https://github.com/gcorso/DiffDock :

    python -m inference --config default_inference_args.yaml \
        --protein_ligand_csv jobs.csv --out_dir results/

Usage:
    python diffdock_jobs.py --relaxed-pdbs-dir ../data/shortlist/relaxed_pdbs --out jobs.csv
"""
import argparse
import csv
import glob
import os

from pfas_substrates import SUBSTRATES


def build_jobs_csv(relaxed_pdbs_dir, out_path, substrate_names=None):
    substrate_names = substrate_names or list(SUBSTRATES)
    pdbs = sorted(glob.glob(f"{relaxed_pdbs_dir}/*.pdb"))
    rows = []
    for pdb in pdbs:
        name = os.path.basename(pdb).replace("_relaxed.pdb", "").replace(".pdb", "")
        abs_path = os.path.abspath(pdb)
        for sub_name in substrate_names:
            smiles = SUBSTRATES[sub_name]["smiles"]
            rows.append([f"{name}__{sub_name}", abs_path, smiles, ""])

    with open(out_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["complex_name", "protein_path", "ligand_description", "protein_sequence"])
        w.writerows(rows)

    return len(rows)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--relaxed-pdbs-dir", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--substrates", nargs="+", default=None,
                    help=f"subset of {list(SUBSTRATES)}, default: all")
    args = p.parse_args()
    n = build_jobs_csv(args.relaxed_pdbs_dir, args.out, args.substrates)
    print(f"wrote {n} jobs to {args.out}")
