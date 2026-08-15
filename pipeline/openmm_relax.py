"""
Molecular dynamics relaxation of shortlisted candidates, as a second, independent
stability check beyond ESMFold self-consistency.

ESMFold agreeing with RFdiffusion's intended structure only tells you two AI
models agree with each other. This runs an actual physics simulation (Amber14
force field, GBN2 implicit solvent, OpenMM) on each candidate and measures how
much the structure drifts under real molecular dynamics. That's a different
kind of evidence, not just a stricter version of the same one.

Protocol, stated plainly: energy minimize, then 100 ps production (50,000 steps
at 2 fs/step) at 300K. That's short by MD standards, a fast first-pass stability
screen, not exhaustive conformational sampling or a folding simulation. Implicit
solvent trades accuracy for speed versus explicit water. Results here say
"didn't immediately fall apart under real physics," not "confirmed stable
long-term" or "confirmed functional."

Requires OpenMM's OpenCL platform to actually reach the GPU (there's no OpenMM
CUDA platform available in the pip package on the machine this was built on;
OpenCL was verified to hit 100% GPU utilization instead -- checked directly via
nvidia-smi during a test run, not assumed).

Usage:
    python openmm_relax.py --shortlist-dir ../data/shortlist \
        --campaign-logs campaign_batch1/logs/campaign_results.jsonl campaign_batch2/logs/campaign_results.jsonl \
        --out-dir ./relaxation
"""
import argparse
import builtins
import json
import csv
import os
import time

from pdbfixer import PDBFixer
from openmm.app import ForceField, Simulation, PDBFile, NoCutoff, HBonds
from openmm import Platform, LangevinMiddleIntegrator
from openmm.unit import kelvin, picosecond, picoseconds, kilojoules_per_mole, angstrom
import numpy as np

# openmm.unit's wildcard-import-friendly namespace shadows the builtin sum() with a
# unit-aware version that raises TypeError on a generator input. Not shadowed here
# since these are explicit imports, but restoring it defensively in case that changes.
sum = builtins.sum

PRODUCTION_STEPS = 50000  # 100 ps at 2 fs/step
TIMESTEP_PS = 0.002
TEMPERATURE_K = 300


def parse_ca(topology, positions_angstrom):
    """positions_angstrom must already be a plain numpy array with units stripped."""
    coords = {}
    for atom in topology.atoms():
        if atom.name == "CA":
            try:
                resnum = int(atom.residue.id)
            except ValueError:
                continue
            coords[resnum] = positions_angstrom[atom.index]
    return coords


def kabsch_rmsd(P, Q):
    P, Q = np.array(P), np.array(Q)
    Pc, Qc = P - P.mean(0), Q - Q.mean(0)
    H = Pc.T @ Qc
    U, S, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    D = np.diag([1, 1, d])
    R = Vt.T @ D @ U.T
    P_aligned = (R @ Pc.T).T + Q.mean(0)
    return float(np.sqrt(np.mean(np.sum((P_aligned - Q) ** 2, axis=1))))


def relax_one(pdb_path, motif_positions, out_pdb_path):
    fixer = PDBFixer(filename=pdb_path)
    fixer.findMissingResidues()
    fixer.findMissingAtoms()
    fixer.addMissingAtoms()
    fixer.addMissingHydrogens(7.0)

    forcefield = ForceField("amber14-all.xml", "implicit/gbn2.xml")
    system = forcefield.createSystem(fixer.topology, nonbondedMethod=NoCutoff, constraints=HBonds)
    integrator = LangevinMiddleIntegrator(TEMPERATURE_K * kelvin, 1 / picosecond, TIMESTEP_PS * picoseconds)
    platform = Platform.getPlatformByName("OpenCL")
    simulation = Simulation(fixer.topology, system, integrator, platform)
    simulation.context.setPositions(fixer.positions)

    state0 = simulation.context.getState(getPositions=True)
    start_ca = parse_ca(fixer.topology, state0.getPositions(asNumpy=True).value_in_unit(angstrom))

    simulation.minimizeEnergy(maxIterations=500)
    min_energy = simulation.context.getState(getEnergy=True).getPotentialEnergy().value_in_unit(kilojoules_per_mole)

    simulation.context.setVelocitiesToTemperature(TEMPERATURE_K * kelvin)
    simulation.step(PRODUCTION_STEPS)

    final_state = simulation.context.getState(getPositions=True, getEnergy=True)
    final_energy = final_state.getPotentialEnergy().value_in_unit(kilojoules_per_mole)
    final_ca = parse_ca(fixer.topology, final_state.getPositions(asNumpy=True).value_in_unit(angstrom))

    common = sorted(set(start_ca) & set(final_ca))
    backbone_drift = kabsch_rmsd([final_ca[r] for r in common], [start_ca[r] for r in common])

    site_drift = None
    if motif_positions and all(p in start_ca and p in final_ca for p in motif_positions):
        site_drift = kabsch_rmsd([final_ca[p] for p in motif_positions], [start_ca[p] for p in motif_positions])

    with open(out_pdb_path, "w") as f:
        PDBFile.writeFile(fixer.topology, final_state.getPositions(), f)

    return dict(n_atoms=fixer.topology.getNumAtoms(), min_energy_kj_mol=min_energy,
                final_energy_kj_mol=final_energy, backbone_drift_A=backbone_drift,
                active_site_drift_A=site_drift)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--shortlist-dir", required=True)
    p.add_argument("--campaign-logs", nargs="+", required=True,
                    help="original campaign_results.jsonl file(s), used to look up each "
                         "candidate's active-site residue positions")
    p.add_argument("--out-dir", required=True)
    args = p.parse_args()

    os.makedirs(f"{args.out_dir}/relaxed_pdbs", exist_ok=True)

    motif_lookup = {}
    for log_path in args.campaign_logs:
        # batch label must match manifest.csv's "batch" column exactly (e.g. "batch1",
        # not "campaign_batch1") -- derived from the grandparent directory name since
        # the log filename itself is identical across batches by convention.
        batch = os.path.basename(os.path.dirname(os.path.dirname(os.path.abspath(log_path)))).replace("campaign_", "")
        for line in open(log_path):
            r = json.loads(line)
            motif_lookup[(batch, r["backbone"], r["seq_idx"])] = r["motif_positions"]

    rows = list(csv.DictReader(open(f"{args.shortlist_dir}/manifest.csv")))
    print(f"Loaded {len(rows)} shortlisted candidates")

    results = []
    for row in rows:
        rank = int(row["rank"])
        gid = row["global_id"]
        key = (row["batch"], row["backbone"], int(row["seq_idx"]))
        motif_positions = motif_lookup.get(key)
        pdb_path = f"{args.shortlist_dir}/pdbs/rank{rank:02d}_{gid}.pdb"
        out_pdb = f"{args.out_dir}/relaxed_pdbs/rank{rank:02d}_{gid}_relaxed.pdb"

        t0 = time.time()
        rec = relax_one(pdb_path, motif_positions, out_pdb)
        rec.update(rank=rank, global_id=gid, elapsed_s=time.time() - t0)
        results.append(rec)
        site_str = f"{rec['active_site_drift_A']:.2f}A" if rec['active_site_drift_A'] is not None else "n/a"
        print(f"[{rank:2d}/{len(rows)}] {gid}: backbone_drift={rec['backbone_drift_A']:.2f}A "
              f"site_drift={site_str} "
              f"({rec['elapsed_s']:.1f}s)", flush=True)

    with open(f"{args.out_dir}/relaxation_results.json", "w") as f:
        json.dump(results, f, indent=2)

    bb = [r["backbone_drift_A"] for r in results]
    site = [r["active_site_drift_A"] for r in results if r["active_site_drift_A"] is not None]
    print(f"\n=== SUMMARY (n={len(results)}) ===")
    print(f"backbone drift: mean={np.mean(bb):.2f}A min={np.min(bb):.2f}A max={np.max(bb):.2f}A")
    if site:
        print(f"active-site drift: mean={np.mean(site):.2f}A min={np.min(site):.2f}A max={np.max(site):.2f}A n={len(site)}")
    print(f"n with backbone drift < 2.0A: {sum(1 for x in bb if x < 2.0)}/{len(bb)}")
    print(f"n with active-site drift < 1.0A: {sum(1 for x in site if x < 1.0)}/{len(site)}")

    os._exit(0)  # same CUDA/OpenCL context teardown hang observed elsewhere in this project


if __name__ == "__main__":
    main()
