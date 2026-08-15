# Chai-1: A Fourth Independent Check, Different Architecture Entirely

Fourth line of evidence, after ESMFold self-consistency, OpenMM MD relaxation, and DiffDock docking. This one asks the same core question ESMFold did — does this sequence fold into a well-defined structure — but with a genuinely different model. Chai-1 is an AlphaFold3-class diffusion model, not a language-model-based folder like ESMFold. Agreement between the two isn't just repeating the same check twice; it's two different methods independently arriving at the same answer.

## Method

- **Tool:** Chai-1 (`chai_lab`, chaidiscovery.com), pip-installable, run via `chai-lab fold`.
- **Setup note:** the published package declares `torch<2.7,>=2.3.1`, and installing it silently downgraded the working `torch==2.11.0+cu128` down to `torch==2.6.0+cu124`, which does not support this GPU's compute capability (`sm_120`) at all (confirmed directly: `RuntimeError: CUDA error: no kernel image is available for execution on the device`). Forced torch back to 2.11.0+cu128 afterward and re-verified both GPU compute and `chai_lab` import together, since it wasn't obvious in advance that the package's actual code was fine with a version 4+ minor releases past what it declares support for. It was.
- **Input:** protein sequence only, no MSA (a designed sequence has no natural evolutionary homologs for an MSA to find anything meaningful in), no template.
- **Metric:** pTM (predicted TM-score) from the model's own `scores.model_idx_0.npz` output, model_idx_0 (Chai-1's top-ranked of 5 samples per fold). Field-standard interpretation: pTM > 0.5 is generally considered a confident fold prediction.
- Note: `chai-lab fold`'s printed "Score" and the npz's `aggregate_score` are a different, undocumented composite metric, not pTM. For a single-chain prediction with nothing to interact with, `iptm` is 0 by construction, and `aggregate_score` appears to weight that heavily, making it look artificially low. Read pTM from the npz directly instead of trusting the CLI's printed score.

## Results (n=30, all shortlisted candidates)

- **30/30 succeeded**, no failures.
- pTM: mean 0.887, range 0.762–0.946.
- **30/30 above the 0.5 confident threshold. 30/30 above 0.7 (high confidence).**

Full per-candidate pTM values in `data/shortlist/chai1_results/*/scores.model_idx_0.npz`; predicted structures (5 per candidate) in the same directories as `.cif` files.

## How to read this

This is the strongest single result across all four validation layers, and it should be read carefully rather than taken as final proof of anything. What it actually shows: a second, architecturally unrelated structure-prediction model looked at these 30 designed sequences and, independently of ESMFold, concluded every one of them folds into a well-defined structure with high confidence. That rules out one specific failure mode — that the ESMFold agreement seen earlier was some kind of ESMFold-specific artifact or blind spot rather than a real property of the sequences. Two independent methods agreeing is meaningfully stronger evidence than either alone.

It does not touch the two questions that actually matter most, which the earlier layers already addressed honestly: whether these designs bind or process PFAS (DiffDock already showed the answer for FAcD-scaffolded designs is no, by design, since the target isn't PFAS), and whether any of this reflects real catalytic activity (nothing here or elsewhere in this repo does, since nothing has been synthesized).

**Raw note:** ran protein-only folds here, not protein+ligand co-folding, which Chai-1 also supports. Co-folding with fluoroacetate/PFOA/PFOS would be a natural next comparison point against DiffDock's docking results (two different methods for the same substrate question), but wasn't done in this pass, given diminishing marginal value once the docking question was already answered.
