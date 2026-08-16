"""
A SECOND, mechanistically different real enzyme target -- and a documented
negative result, not a working recipe to copy blindly.

Everything else in this repo scaffolds fluoroacetate dehalogenase (FAcD, a
haloACID dehalogenase -- activated single C-F bond next to a carboxylate).
This targets haloalkane dehalogenase (DhlA, PDB 2HAD, Xanthobacter
autotrophicus) instead -- a real, structurally verified enzyme from a
DIFFERENT candidate family named in the PFAS-engineering review literature.
DhlA processes unactivated alkyl halides (its native substrate is
1,2-dichloroethane) in a hydrophobic pocket, mechanistically closer to a long
inert perfluorocarbon chain than FAcD's carboxylate-adjacent single-F-bond
chemistry. The real hypothesis: does docking against real PFAS substrates
score any better against THIS scaffold family than it did against FAcD (which
scored 0/30 high-confidence for PFOA/PFOS)?

RESULT, both tried, both negative: this motif-scaffolding approach did not
produce a working DhlA pocket, with either the 3-residue catalytic triad
(Asp124/Asp260/His289) or a corrected 5-residue set that also includes the
real chloride-binding tryptophans (Trp125, Trp175, verified via UniProt
P22643). Both versions scored 0/N DiffDock high-confidence for DhlA's OWN
native substrate, not just for PFAS -- a different, more informative failure
mode than FAcD's clean "binds its own substrate, doesn't bind PFAS" result.
Full writeup: research/dhla_second_target.md. The original hypothesis about
haloalkane dehalogenases remains genuinely untested, because this method
can't currently build a working DhlA scaffold to test it with -- not because
the hypothesis itself was refuted.

The 5-residue version below is what's checked in (the corrected attempt);
the original 3-residue version is documented in the research writeup for the
full history, not preserved as a second code path here.

Catalytic residues verified directly against the downloaded 2HAD structure
file, not just UniProt's annotation. No bound ligand in 2HAD (only water),
same situation as FAcD's 1Y37 -- plain motif scaffolding, no substrate-contact
potential.

Runs the full validated stack end to end, unattended:
  RFdiffusion -> ProteinMPNN -> ESMFold filter -> curate shortlist ->
  OpenMM relax -> DiffDock (1,2-dichloroethane + PFOA + PFOS) -> Chai-1 fold

IMPORTANT: each stage must run as its own process (see
run_dhla_overnight.sh) -- stages 1 and 3 call os._exit(0) internally to work
around a real torch/CUDA and OpenCL context teardown hang observed on this
machine. Chaining stages in one long-lived process hard-exits after stage 1.
"""
import subprocess, json, os, time, pickle, glob, csv, re, sys

BASE = os.path.expanduser("~/biocompiler")
RFDIFF = f"{BASE}/RFdiffusion"
MPNN = f"{BASE}/ProteinMPNN"
CAMPAIGN = f"{BASE}/dhla_campaign_v2"
PY = f"{BASE}/venv/bin/python3"
DIFFDOCK_VENV = f"{BASE}/diffdock_venv/bin/python3"
DIFFDOCK_DIR = f"{BASE}/DiffDock"
CHAI_BIN = f"{BASE}/chai_venv/bin/chai-lab"

N_BACKBONES = 200
SEQS_PER_BACKBONE = 9
SAMPLING_TEMPS = ["0.1", "0.2", "0.3"]
PLDDT_PASS = 65.0
RMSD_PASS = 2.0
SHORTLIST_N = 30
MAX_PER_BACKBONE = 3

# Catalytic triad (Asp124 nucleophile, Asp260 proton donor, His289 proton
# acceptor) PLUS the two chloride/halide-binding tryptophans (Trp125, Trp175),
# verified via UniProt P22643 and directly against the 2HAD structure file.
# Fixing only the triad (an earlier attempt, see research/dhla_second_target.md)
# came back 0/30 high-confidence DiffDock even for DhlA's own native substrate.
# This 5-residue version was a real attempt to fix that; it didn't work either
# (0/4 on a small check) -- kept as the more scientifically complete scaffold
# despite that, since it's the more correct representation of DhlA's real
# binding site regardless of whether this scaffolding method can use it well.
# 124 and 125 are adjacent, scaffolded as one fixed block.
FIXED_RES = [124, 125, 175, 260, 289]
CONTIG = "[10-40/A124-125/30-70/A175-175/50-110/A260-260/15-40/A289-289/10-40]"
INPUT_PDB = "2had.pdb"

SUBSTRATES = {
    "12dichloroethane": "C(CCl)Cl",  # DhlA's real native substrate, verified via PubChem
    "PFOA": "C(=O)(C(C(C(C(C(C(C(F)(F)F)(F)F)(F)F)(F)F)(F)F)(F)F)(F)F)O",
    "PFOS": "C(C(C(C(C(F)(F)S(=O)(=O)O)(F)F)(F)F)(F)F)(C(C(C(F)(F)F)(F)F)(F)F)(F)F",
}

for d in ["rfdiffusion_outputs", "mpnn_work", "esmfold_outputs", "candidates", "logs",
          "shortlist/pdbs", "relaxed_pdbs", "diffdock_results", "chai1_results"]:
    os.makedirs(f"{CAMPAIGN}/{d}", exist_ok=True)

log_f = open(f"{CAMPAIGN}/logs/campaign.log", "a")
def log(stage, msg):
    line = f"[{time.strftime('%H:%M:%S')}] [{stage}] {msg}"
    print(line, flush=True)
    log_f.write(line + "\n")
    log_f.flush()

def run(cmd, **kw):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, **kw)


# ============================================================
# STAGE 1: RFdiffusion -> ProteinMPNN -> ESMFold campaign
# ============================================================
def stage1_generate():
    import torch
    from transformers import AutoTokenizer, EsmForProteinFolding
    import numpy as np

    log("S1", f"Loading ESMFold...")
    tokenizer = AutoTokenizer.from_pretrained("facebook/esmfold_v1")
    model = EsmForProteinFolding.from_pretrained("facebook/esmfold_v1", low_cpu_mem_usage=True).cuda()
    model.esm = model.esm.half()
    model.trunk.set_chunk_size(64)
    model.eval()
    log("S1", "ESMFold loaded")

    def parse_ca(path):
        coords = {}
        with open(path) as f:
            for line in f:
                if line.startswith("ATOM") and line[12:16].strip() == "CA":
                    resnum = int(line[22:26])
                    coords[resnum] = np.array([float(line[30:38]), float(line[38:46]), float(line[46:54])])
        return coords

    def kabsch(P, Q):
        Pc, Qc = P - P.mean(0), Q - Q.mean(0)
        H = Pc.T @ Qc
        U, S, Vt = np.linalg.svd(H)
        d = np.sign(np.linalg.det(Vt.T @ U.T))
        D = np.diag([1, 1, d])
        R = Vt.T @ D @ U.T
        return (R @ Pc.T).T + Q.mean(0)

    n_candidates, n_total_seqs = 0, 0
    for i in range(1, N_BACKBONES + 1):
        prefix = f"design_{i:04d}"
        docker_cmd = f"""
        docker run --rm --gpus all \
          -v {RFDIFF}/models:/app/RFdiffusion/models \
          -v {RFDIFF}/examples/input_pdbs:/app/RFdiffusion/examples/input_pdbs \
          -v {CAMPAIGN}/rfdiffusion_outputs:/app/RFdiffusion/examples/campaign_outputs \
          -w /app/RFdiffusion/examples \
          rfdiffusion-rtx5090:latest \
          conda run -n rfdiffusion --no-capture-output python ../scripts/run_inference.py \
          inference.output_prefix=campaign_outputs/{prefix} \
          inference.input_pdb=input_pdbs/{INPUT_PDB} \
          "contigmap.contigs={CONTIG}" \
          inference.ckpt_override_path=../models/ActiveSite_ckpt.pt \
          inference.num_designs=1
        """
        r = run(docker_cmd)
        pdb_path = f"{CAMPAIGN}/rfdiffusion_outputs/{prefix}_0.pdb"
        trb_path = f"{CAMPAIGN}/rfdiffusion_outputs/{prefix}_0.trb"
        if not os.path.exists(pdb_path):
            log("S1", f"  RFdiffusion FAILED for {prefix}")
            continue

        trb = pickle.load(open(trb_path, "rb"))
        hal_positions = [int(p[1]) for p in trb["con_hal_pdb_idx"]]

        single_dir = f"{CAMPAIGN}/rfdiffusion_outputs/{prefix}_single"
        os.makedirs(single_dir, exist_ok=True)
        run(f"cp {pdb_path} {single_dir}/")
        parsed = f"{CAMPAIGN}/mpnn_work/{prefix}_parsed.jsonl"
        fixed = f"{CAMPAIGN}/mpnn_work/{prefix}_fixed.jsonl"
        run(f"{PY} {MPNN}/helper_scripts/parse_multiple_chains.py --input_path {single_dir} --output_path {parsed}")
        pos_str = " ".join(str(p) for p in hal_positions)
        run(f"{PY} {MPNN}/helper_scripts/make_fixed_positions_dict.py "
            f"--input_path {parsed} --output_path {fixed} --chain_list A --position_list \"{pos_str}\"")

        all_seqs = []
        for temp in SAMPLING_TEMPS:
            out_dir = f"{CAMPAIGN}/mpnn_work/{prefix}_T{temp}"
            r = run(f"{PY} {MPNN}/protein_mpnn_run.py "
                    f"--jsonl_path {parsed} --fixed_positions_jsonl {fixed} "
                    f"--out_folder {out_dir} --num_seq_per_target {SEQS_PER_BACKBONE // len(SAMPLING_TEMPS)} "
                    f"--sampling_temp {temp} --seed {i} --batch_size 1")
            fa_files = glob.glob(f"{out_dir}/seqs/*.fa")
            if not fa_files:
                continue
            with open(fa_files[0]) as f:
                lines = f.read().strip().split("\n")
            recs = [(lines[j][1:], lines[j + 1]) for j in range(0, len(lines), 2) if lines[j].startswith(">T=")]
            all_seqs.extend(recs)

        ref = parse_ca(pdb_path)
        ref_resnums = sorted(ref.keys())
        ref_coords = np.array([ref[r_] for r_ in ref_resnums])
        idx = [ref_resnums.index(p) for p in hal_positions]

        for j, (header, seq) in enumerate(all_seqs):
            n_total_seqs += 1
            with torch.no_grad():
                inputs = tokenizer([seq], return_tensors="pt", add_special_tokens=False)
                inputs = {k: v.cuda() for k, v in inputs.items()}
                out = model(**inputs)
            pl = out["plddt"][0]
            per_res = pl.mean(dim=-1) if pl.dim() == 2 else pl
            mean_plddt = per_res.mean().item() * (100 if per_res.max() <= 1.5 else 1)

            fold_pdb_str = model.infer_pdb(seq)
            fold_path = f"{CAMPAIGN}/esmfold_outputs/{prefix}_seq{j}.pdb"
            with open(fold_path, "w") as f:
                f.write(fold_pdb_str)

            pred = parse_ca(fold_path)
            pred_resnums = sorted(pred.keys())
            if pred_resnums != ref_resnums:
                continue
            pred_coords = np.array([pred[r_] for r_ in pred_resnums])
            pred_aligned = kabsch(pred_coords, ref_coords)
            site_rmsd = float(np.sqrt(np.mean(np.sum((pred_aligned[idx] - ref_coords[idx]) ** 2, axis=1))))

            record = dict(backbone=prefix, seq_idx=j, header=header, seq=seq,
                           mean_plddt=mean_plddt, active_site_rmsd=site_rmsd,
                           motif_positions=hal_positions, fold_pdb=fold_path, backbone_pdb=pdb_path)
            with open(f"{CAMPAIGN}/logs/results.jsonl", "a") as lf:
                lf.write(json.dumps(record) + "\n")

            if mean_plddt >= PLDDT_PASS and site_rmsd <= RMSD_PASS:
                n_candidates += 1

        run(f"rm -rf {single_dir}")
        if i % 20 == 0 or i == N_BACKBONES:
            log("S1", f"  {i}/{N_BACKBONES} backbones, {n_total_seqs} seqs, {n_candidates} candidates")

    log("S1", f"COMPLETE: {N_BACKBONES} backbones, {n_total_seqs} sequences, {n_candidates} candidates")
    os._exit(0)  # force-exit in a subprocess wrapper; see stage runner below


# ============================================================
# STAGE 2: curate shortlist
# ============================================================
def stage2_curate():
    recs = [json.loads(l) for l in open(f"{CAMPAIGN}/logs/results.jsonl")]
    passed = [r for r in recs if r["mean_plddt"] >= PLDDT_PASS and r["active_site_rmsd"] <= RMSD_PASS]
    passed.sort(key=lambda r: (r["active_site_rmsd"], -r["mean_plddt"]))

    selected, per_backbone = [], {}
    for r in passed:
        k = r["backbone"]
        if per_backbone.get(k, 0) >= MAX_PER_BACKBONE:
            continue
        selected.append(r)
        per_backbone[k] = per_backbone.get(k, 0) + 1
        if len(selected) >= SHORTLIST_N:
            break

    log("S2", f"Total passed: {len(passed)}, selected: {len(selected)} from {len(per_backbone)} backbones")

    with open(f"{CAMPAIGN}/shortlist/manifest.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["rank", "global_id", "backbone", "seq_idx", "mean_plddt", "active_site_rmsd", "seq_length", "sequence"])
        for i, r in enumerate(selected, 1):
            w.writerow([i, r["backbone"] + f"_seq{r['seq_idx']}", r["backbone"], r["seq_idx"],
                        f"{r['mean_plddt']:.1f}", f"{r['active_site_rmsd']:.2f}", len(r["seq"]), r["seq"]])

    for i, r in enumerate(selected, 1):
        gid = r["backbone"] + f"_seq{r['seq_idx']}"
        run(f"cp {r['fold_pdb']} {CAMPAIGN}/shortlist/pdbs/rank{i:02d}_{gid}.pdb")

    return selected


# ============================================================
# STAGE 3: OpenMM relax (run in the main venv, not a subprocess -- needs its own imports)
# ============================================================
def stage3_relax(selected):
    import builtins
    from pdbfixer import PDBFixer
    from openmm.app import ForceField, Simulation, PDBFile, NoCutoff, HBonds
    from openmm import Platform, LangevinMiddleIntegrator
    from openmm.unit import kelvin, picosecond, picoseconds, kilojoules_per_mole, angstrom
    import numpy as np
    sum_ = builtins.sum

    def parse_ca(topology, positions_angstrom):
        coords = {}
        for atom in topology.atoms():
            if atom.name == "CA":
                try:
                    coords[int(atom.residue.id)] = positions_angstrom[atom.index]
                except ValueError:
                    continue
        return coords

    def kabsch(P, Q):
        P, Q = np.array(P), np.array(Q)
        Pc, Qc = P - P.mean(0), Q - Q.mean(0)
        H = Pc.T @ Qc
        U, S, Vt = np.linalg.svd(H)
        d = np.sign(np.linalg.det(Vt.T @ U.T))
        D = np.diag([1, 1, d])
        R = Vt.T @ D @ U.T
        return float(np.sqrt(np.mean(np.sum(((R @ Pc.T).T + Q.mean(0) - Q) ** 2, axis=1))))

    results = []
    for i, r in enumerate(selected, 1):
        gid = r["backbone"] + f"_seq{r['seq_idx']}"
        pdb_path = f"{CAMPAIGN}/shortlist/pdbs/rank{i:02d}_{gid}.pdb"
        out_pdb = f"{CAMPAIGN}/relaxed_pdbs/rank{i:02d}_{gid}_relaxed.pdb"

        fixer = PDBFixer(filename=pdb_path)
        fixer.findMissingResidues(); fixer.findMissingAtoms(); fixer.addMissingAtoms(); fixer.addMissingHydrogens(7.0)
        forcefield = ForceField("amber14-all.xml", "implicit/gbn2.xml")
        system = forcefield.createSystem(fixer.topology, nonbondedMethod=NoCutoff, constraints=HBonds)
        integrator = LangevinMiddleIntegrator(300 * kelvin, 1 / picosecond, 0.002 * picoseconds)
        platform = Platform.getPlatformByName("OpenCL")
        simulation = Simulation(fixer.topology, system, integrator, platform)
        simulation.context.setPositions(fixer.positions)

        start_ca = parse_ca(fixer.topology, simulation.context.getState(getPositions=True).getPositions(asNumpy=True).value_in_unit(angstrom))
        simulation.minimizeEnergy(maxIterations=500)
        simulation.context.setVelocitiesToTemperature(300 * kelvin)
        simulation.step(50000)
        final_state = simulation.context.getState(getPositions=True)
        final_ca = parse_ca(fixer.topology, final_state.getPositions(asNumpy=True).value_in_unit(angstrom))

        common = sorted(set(start_ca) & set(final_ca))
        backbone_drift = kabsch([final_ca[c] for c in common], [start_ca[c] for c in common])
        motif = r["motif_positions"]
        site_drift = kabsch([final_ca[p] for p in motif], [start_ca[p] for p in motif]) if all(p in start_ca and p in final_ca for p in motif) else None

        with open(out_pdb, "w") as f:
            PDBFile.writeFile(fixer.topology, final_state.getPositions(), f)

        results.append(dict(rank=i, global_id=gid, backbone_drift_A=backbone_drift, active_site_drift_A=site_drift))
        log("S3", f"  [{i}/{len(selected)}] {gid}: backbone={backbone_drift:.2f}A site={site_drift}")

    with open(f"{CAMPAIGN}/relaxed_pdbs/relaxation_results.json", "w") as f:
        json.dump(results, f, indent=2)
    bb = [x["backbone_drift_A"] for x in results]
    site = [x["active_site_drift_A"] for x in results if x["active_site_drift_A"] is not None]
    log("S3", f"COMPLETE: backbone<2.0A: {sum_(1 for x in bb if x<2.0)}/{len(bb)}, site<1.0A: {sum_(1 for x in site if x<1.0)}/{len(site)}")
    os._exit(0)  # same OpenCL/CUDA context teardown hang risk as stage 1


# ============================================================
# STAGE 4: DiffDock (run as subprocess with the DiffDock venv)
# ============================================================
def stage4_diffdock():
    jobs_csv = f"{CAMPAIGN}/diffdock_jobs.csv"
    rows = []
    for pdb in sorted(glob.glob(f"{CAMPAIGN}/relaxed_pdbs/*.pdb")):
        name = os.path.basename(pdb).replace("_relaxed.pdb", "")
        for sub, smiles in SUBSTRATES.items():
            rows.append([f"{name}__{sub}", os.path.abspath(pdb), smiles, ""])
    with open(jobs_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["complex_name", "protein_path", "ligand_description", "protein_sequence"])
        w.writerows(rows)
    log("S4", f"{len(rows)} docking jobs")

    r = run(f"cd {DIFFDOCK_DIR} && {DIFFDOCK_VENV} -m inference --config default_inference_args.yaml "
            f"--protein_ligand_csv {jobs_csv} --out_dir {CAMPAIGN}/diffdock_results")
    log("S4", f"DiffDock exit: returncode={r.returncode}")
    if r.returncode != 0:
        log("S4", f"stderr tail: {r.stderr[-1000:]}")

    results = []
    for d in sorted(os.listdir(f"{CAMPAIGN}/diffdock_results")):
        dpath = f"{CAMPAIGN}/diffdock_results/{d}"
        if not os.path.isdir(dpath):
            continue
        files = glob.glob(f"{dpath}/rank1_confidence*.sdf")
        conf = None
        if files:
            m = re.search(r"confidence(-?[\d.]+)\.sdf", files[0])
            conf = float(m.group(1)) if m else None
        results.append(dict(complex=d, top_confidence=conf))
    with open(f"{CAMPAIGN}/diffdock_results/summary.json", "w") as f:
        json.dump(results, f, indent=2)

    import statistics
    by_sub = {}
    for x in results:
        if x["top_confidence"] is None:
            continue
        sub = x["complex"].split("__")[-1]
        by_sub.setdefault(sub, []).append(x["top_confidence"])
    for sub, vals in by_sub.items():
        high = sum(1 for v in vals if v > 0)
        log("S4", f"  {sub}: n={len(vals)} mean={statistics.mean(vals):.2f} high_conf(c>0)={high}/{len(vals)}")


# ============================================================
# STAGE 5: Chai-1
# ============================================================
def stage5_chai():
    rows = list(csv.DictReader(open(f"{CAMPAIGN}/shortlist/manifest.csv")))
    results = []
    for i, row in enumerate(rows, 1):
        gid = row["global_id"]
        fasta = f"{CAMPAIGN}/chai1_results/{gid}.fasta"
        with open(fasta, "w") as f:
            f.write(f">protein|name={gid}\n{row['sequence']}\n")
        out_dir = f"{CAMPAIGN}/chai1_results/{gid}"
        r = run(f"{CHAI_BIN} fold {fasta} {out_dir}")
        if r.returncode != 0:
            log("S5", f"  [{i}/{len(rows)}] {gid}: FAILED")
            results.append(dict(gid=gid, ok=False))
            continue
        import numpy as np
        d = np.load(f"{out_dir}/scores.model_idx_0.npz")
        ptm = float(d["ptm"][0])
        results.append(dict(gid=gid, ok=True, ptm=ptm))
        log("S5", f"  [{i}/{len(rows)}] {gid}: ptm={ptm:.3f}")

    with open(f"{CAMPAIGN}/chai1_results/summary.json", "w") as f:
        json.dump(results, f, indent=2)
    ptms = [r["ptm"] for r in results if r.get("ok")]
    if ptms:
        log("S5", f"COMPLETE: pTM mean={sum(ptms)/len(ptms):.3f} n>0.7={sum(1 for p in ptms if p>0.7)}/{len(ptms)}")


# ============================================================
# ORCHESTRATION
#
# Each stage MUST run as its own process, invoked separately (see
# run_dhla_overnight.sh) -- stages 1 and 3 call os._exit(0) internally to work
# around a real, previously-observed torch/CUDA and OpenCL context teardown
# hang on this machine. Chaining all stages in one long-lived process would
# hard-exit after stage 1 and never reach the rest.
# ============================================================
if __name__ == "__main__":
    stage = sys.argv[1]

    if stage == "1":
        log("MAIN", "=== STAGE 1: RFdiffusion/ProteinMPNN/ESMFold campaign ===")
        stage1_generate()  # calls os._exit(0) itself when done

    elif stage == "2":
        log("MAIN", "=== STAGE 2: curate shortlist ===")
        stage2_curate()

    elif stage == "3":
        log("MAIN", "=== STAGE 3: OpenMM relaxation ===")
        recs = [json.loads(l) for l in open(f"{CAMPAIGN}/logs/results.jsonl")]
        rows = list(csv.DictReader(open(f"{CAMPAIGN}/shortlist/manifest.csv")))
        selected = [next(r for r in recs if r["backbone"] == row["backbone"] and str(r["seq_idx"]) == row["seq_idx"])
                    for row in rows]
        stage3_relax(selected)  # calls os._exit(0) itself when done

    elif stage == "4":
        log("MAIN", "=== STAGE 4: DiffDock ===")
        stage4_diffdock()

    elif stage == "5":
        log("MAIN", "=== STAGE 5: Chai-1 ===")
        stage5_chai()

    log("MAIN", f"=== STAGE {stage} COMPLETE ===")
