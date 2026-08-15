# DiffDock: Substrate Docking Against the 30 Candidates

A third independent check, after ESMFold self-consistency and OpenMM MD relaxation. This one asks a different question than the first two: not "is the structure stable," but "does a substrate molecule actually fit the designed pocket." Real substrates, real docking, real (if honest and mixed) results.

## Method

- **Tool:** DiffDock (github.com/gcorso/DiffDock), a diffusion-based docking model.
- **Setup note:** DiffDock's own pinned environment (PyTorch 1.13.1 + CUDA 11.7, from 2022) doesn't work on this hardware, same class of problem RFdiffusion had. Rebuilt against the already-working modern stack (PyTorch 2.11.0+cu128) instead. `torch-scatter`/`torch-cluster`/`torch-sparse` all had prebuilt wheels for that exact torch version, which made this tractable. Full dependency list and the rebuild notes are in `pipeline/`.
- **Inputs:** all 30 relaxed candidate structures (from `data/shortlist/relaxed_pdbs/`, i.e. post-MD, not the raw ESMFold predictions), each docked against three real substrates:
  - **fluoroacetate**, FAcD's actual native substrate, verified SMILES
  - **PFOA** and **PFOS**, the two PFAS compounds covered by the EPA's 2024 drinking water rule, verified SMILES
- **Protocol:** DiffDock's default inference config (20 diffusion steps, 10 samples per complex), unmodified. 90 total docking runs (30 candidates × 3 substrates).
- **Metric:** DiffDock's own confidence score on the top-ranked pose per complex. Per DiffDock's documented calibration: c > 0 is "high confidence," -1.5 < c < 0 is "moderate," below that is low.

## Results (n=30 per substrate, 90 total)

| Substrate | Mean confidence | Range | High confidence (c>0) | Moderate |
|---|---|---|---|---|
| Fluoroacetate | -0.10 | -0.63 to 0.29 | **9/30** | 21/30 |
| PFOA | -2.00 | -3.79 to -0.61 | **0/30** | 8/30 |
| PFOS | -2.11 | -3.13 to -1.04 | **0/30** | 5/30 |

Full per-complex results in `data/shortlist/diffdock_summary.json`; all 90 raw docking outputs (10 poses each) in `data/shortlist/diffdock_results/`.

## How to read this, honestly

This is not a disappointing result. It's the expected one, and now it's measured instead of assumed. Every candidate in this shortlist was scaffolded around fluoroacetate dehalogenase's real catalytic site, and the docking confirms that geometry: fluoroacetate fits, PFOA and PFOS don't. That's real, independent, quantitative evidence for exactly the caveat already stated everywhere else in this repo, that FAcD is a literature-endorsed stand-in target and not a PFAS-relevant one on its own. If PFOA/PFOS had docked *well*, that would actually have been the surprising result worth double-checking, since nothing about these designs was built with PFAS geometry or chemistry in mind.

What this does establish: the designed pocket is real and selective, not just a generic cavity that anything would sit in. 9 of 30 candidates dock with a real small molecule at high confidence by an independent, non-AI-structure-prediction model. That's worth something on its own, separate from the PFAS question. It's evidence the "enzyme-shaped" part of this actually worked, even though the "PFAS-shaped" part still doesn't exist and won't until a real PFAS-active structural target becomes available (see `enzyme_science.md`, `rdhA`).

**Raw note:** docking confidence is not binding affinity, and binding (even if it existed) is not catalysis. DiffDock estimates whether a pose is *geometrically plausible*, it says nothing about reaction chemistry, transition-state stabilization, or turnover. A high-confidence PFOA dock, had one occurred, would not have meant "this enzyme degrades PFOA." Its absence here doesn't close the door either, it's simply consistent with everything else already known about why FAcD is the wrong substrate profile for real PFAS.
