"""
ProteinMPNN sequence design, with the RFdiffusion-fixed motif positions held fixed
so the catalytic residues aren't mutated away.
"""
import subprocess
import os
import glob

DEFAULT_TEMPS = ["0.1", "0.2", "0.3"]


def run(cmd, **kw):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, **kw)


def design_sequences(mpnn_dir, py_bin, backbone_pdb, motif_positions, work_dir,
                      seqs_per_temp=3, temps=None, seed=0, chain="A"):
    """
    Parses a single backbone PDB, fixes the given 1-indexed chain-A residue positions,
    and generates `seqs_per_temp` sequences at each sampling temperature in `temps`.

    Returns a list of (header, sequence) tuples. The parent/template sequence
    (header not starting with "T=") is excluded — those are ProteinMPNN's echo of
    the input structure, not a design.
    """
    temps = temps or DEFAULT_TEMPS
    prefix = os.path.splitext(os.path.basename(backbone_pdb))[0]

    single_dir = f"{work_dir}/{prefix}_single"
    os.makedirs(single_dir, exist_ok=True)
    run(f"cp {backbone_pdb} {single_dir}/")

    parsed = f"{work_dir}/{prefix}_parsed.jsonl"
    fixed = f"{work_dir}/{prefix}_fixed.jsonl"
    run(f"{py_bin} {mpnn_dir}/helper_scripts/parse_multiple_chains.py "
        f"--input_path {single_dir} --output_path {parsed}")

    pos_str = " ".join(str(p) for p in motif_positions)
    run(f"{py_bin} {mpnn_dir}/helper_scripts/make_fixed_positions_dict.py "
        f"--input_path {parsed} --output_path {fixed} --chain_list {chain} "
        f'--position_list "{pos_str}"')

    all_seqs = []
    for temp in temps:
        out_dir = f"{work_dir}/{prefix}_T{temp}"
        result = run(f"{py_bin} {mpnn_dir}/protein_mpnn_run.py "
                      f"--jsonl_path {parsed} --fixed_positions_jsonl {fixed} "
                      f"--out_folder {out_dir} --num_seq_per_target {seqs_per_temp} "
                      f"--sampling_temp {temp} --seed {seed} --batch_size 1")
        fa_files = glob.glob(f"{out_dir}/seqs/*.fa")
        if not fa_files:
            print(f"ProteinMPNN failed at T={temp}: {result.stderr[-300:]}")
            continue
        with open(fa_files[0]) as f:
            lines = f.read().strip().split("\n")
        recs = [(lines[j][1:], lines[j + 1]) for j in range(0, len(lines), 2)
                if lines[j].startswith(">T=")]
        all_seqs.extend(recs)

    run(f"rm -rf {single_dir}")
    return all_seqs
