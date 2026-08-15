# Molecular Dynamics Relaxation: A Second, Independent Stability Check

Everything in `data/shortlist/` up to this point was validated one way: RFdiffusion proposes a backbone, ProteinMPNN designs a sequence for it, ESMFold independently predicts what that sequence actually folds into. When ESMFold agrees with the intended shape, that's a real signal, but it's still two AI models agreeing with each other. This adds a different kind of evidence: does the structure hold up under an actual physics simulation.

## Method, stated plainly

- **Structure prep:** PDBFixer, adding missing atoms and hydrogens (pH 7.0).
- **Force field:** Amber14, with GBN2 implicit solvent (not explicit water, for speed).
- **Protocol:** energy minimization (500 iterations), then 100 ps of production dynamics (50,000 steps at 2 fs/step, Langevin integrator, 300K).
- **Platform:** OpenCL. There's no OpenMM CUDA platform available in the pip package on the machine this ran on; OpenCL was checked directly (`nvidia-smi` showed 100% GPU utilization during a real run, not assumed to be using the GPU).
- **Metric:** Kabsch-aligned CA RMSD between the starting structure and the structure after 100 ps, both for the whole backbone and for just the three catalytic residues.

**What this protocol does and doesn't tell you, honestly:** 100 ps is short by molecular dynamics standards. This is a fast first-pass stability screen, not exhaustive conformational sampling and not a folding simulation. Implicit solvent is faster than explicit water but less physically accurate. A structure passing this check means "didn't immediately fall apart under real physics." It does not mean "confirmed stable long-term" and it says nothing about function or activity.

## Results (n=30, all shortlisted candidates)

- Backbone drift: mean 1.40 Å, range 0.95–2.04 Å
- Active-site drift: mean 0.77 Å, range 0.09–1.54 Å
- 29/30 held backbone drift under 2.0 Å
- 23/30 held active-site drift under 1.0 Å
- 6/30 held active-site drift under 0.5 Å

Full per-candidate numbers in `data/shortlist/relaxation_results.json`; relaxed structures in `data/shortlist/relaxed_pdbs/`.

## How to read this

This is a positive result, and it's independent evidence in a real sense: nothing about the OpenMM simulation depends on ESMFold's own prediction being right, it's a separate physical model. Most candidates held their catalytic geometry reasonably tight under real dynamics, which is exactly what you'd want to see before spending real lab resources on any of them.

It is still not activity data. A structure that stays put for 100 ps of implicit-solvent dynamics has cleared a real bar, a low one relative to what would actually be needed to claim a working enzyme. The next real bar is a wet lab.

**Raw note:** the script that generated the checked-in numbers here (a one-off, machine-specific version) is not what's in `pipeline/openmm_relax.py`. The version in the repo was cleaned up for reuse afterward, and testing that cleanup caught a real bug: it derived batch labels from the log file path differently than `manifest.csv` already used, silently returning `None` for every active-site drift. Caught before being shipped, not after. The numbers above come from the original run, which didn't have this bug.
