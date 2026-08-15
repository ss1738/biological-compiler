"""
RFdiffusion setup, target definition, and backbone generation.

Target: fluoroacetate dehalogenase (FAcD), PDB 1Y37, chain A.
Catalytic triad verified directly against the downloaded structure file (not just
the UniProt annotation) — see research/enzyme_science.md for how that was checked.

This is a stand-in target, not a PFAS-specific enzyme. See README.md and
research/enzyme_science.md for why it was chosen and what it doesn't prove.
"""
import subprocess
import os
import pickle

FIXED_RESIDUES = [104, 128, 271]  # Asp104 (nucleophile), Asp128 (structural), His271 (proton acceptor)
CONTIG = "[10-40/A104-104/15-40/A128-128/80-160/A271-271/10-40]"
INPUT_PDB = "1y37.pdb"  # fetched from https://files.rcsb.org/download/1Y37.pdb
CKPT_OVERRIDE = "ActiveSite_ckpt.pt"  # RFdiffusion's small-motif-scaffolding fine-tune


def run(cmd, **kw):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, **kw)


def validate_setup(rfdiffusion_dir, models_dir):
    """
    Checks that the docker image and weights this pipeline depends on actually exist
    before running anything. Doesn't guarantee the docker daemon/GPU are reachable —
    just that the expected files are present.
    """
    problems = []
    input_pdb_path = f"{rfdiffusion_dir}/examples/input_pdbs/{INPUT_PDB}"
    if not os.path.exists(input_pdb_path):
        problems.append(f"missing input PDB: {input_pdb_path}")
    ckpt_path = f"{models_dir}/{CKPT_OVERRIDE}"
    if not os.path.exists(ckpt_path):
        problems.append(f"missing checkpoint: {ckpt_path}")
    r = run("docker image inspect rfdiffusion-rtx5090:latest")
    if r.returncode != 0:
        problems.append("docker image 'rfdiffusion-rtx5090:latest' not found — build it from docker/RTX-5090.dockerfile first")
    return problems


def generate_backbone(rfdiffusion_dir, models_dir, output_dir, prefix, seed=None):
    """
    Runs one RFdiffusion design scaffolding the fixed catalytic triad. Returns
    (pdb_path, trb_path) if it succeeded, (None, None) if it failed — check
    stderr on the returned subprocess result for why.
    """
    docker_cmd = f"""
    docker run --rm --gpus all \
      -v {models_dir}:/app/RFdiffusion/models \
      -v {rfdiffusion_dir}/examples/input_pdbs:/app/RFdiffusion/examples/input_pdbs \
      -v {output_dir}:/app/RFdiffusion/examples/campaign_outputs \
      -w /app/RFdiffusion/examples \
      rfdiffusion-rtx5090:latest \
      conda run -n rfdiffusion --no-capture-output python ../scripts/run_inference.py \
      inference.output_prefix=campaign_outputs/{prefix} \
      inference.input_pdb=input_pdbs/{INPUT_PDB} \
      "contigmap.contigs={CONTIG}" \
      inference.ckpt_override_path=../models/{CKPT_OVERRIDE} \
      inference.num_designs=1
    """
    result = run(docker_cmd)
    pdb_path = f"{output_dir}/{prefix}_0.pdb"
    trb_path = f"{output_dir}/{prefix}_0.trb"
    if not os.path.exists(pdb_path):
        return None, None, result
    return pdb_path, trb_path, result


def load_motif_positions(trb_path):
    """
    Reads where RFdiffusion actually placed the fixed motif in the new backbone
    (this moves every run — con_hal_pdb_idx is the ground truth, not FIXED_RESIDUES,
    which only describes the *original* positions in 1Y37).
    """
    trb = pickle.load(open(trb_path, "rb"))
    return [int(p[1]) for p in trb["con_hal_pdb_idx"]]
