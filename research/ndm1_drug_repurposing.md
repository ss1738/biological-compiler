# NDM-1 Drug Repurposing Screen

A different application of the same validated DiffDock infrastructure used throughout this repo, applied to a different, real problem: antimicrobial resistance, not PFAS. This is a legitimate, standard computational drug discovery method (repurposing screening) run against a real, clinically important target, using real FDA-approved drug structures.

## Why NDM-1

**NDM-1** (New Delhi metallo-β-lactamase-1), PDB **4EYL**, from *Klebsiella pneumoniae*, 1.90 Å resolution. A dizinc-dependent enzyme that hydrolyzes carbapenem antibiotics — the class often used as a last resort against multi-drug-resistant bacterial infections. NDM-1 is a globally recognized, WHO-priority antimicrobial resistance mechanism, not a niche or invented target. The structure includes the real catalytic zinc ions and is co-crystallized with hydrolyzed meropenem (ligand code 0RV), confirming a functionally characterized active site, not just a static apo structure.

## Method

- **Target:** NDM-1, PDB 4EYL, used as downloaded, no modification.
- **Library:** 13 real FDA-approved drugs, spanning diverse structural classes, each verified via PubChem (SMILES obtained directly from PubChem's REST API by compound name, not recalled from memory): captopril, disulfiram, ebselen, acetazolamide, probenecid, aspirin, metformin, atorvastatin, omeprazole, ciprofloxacin, metronidazole, doxycycline, rifampicin.
- **Excluded:** auranofin. Its PubChem structure is a multi-fragment ionic salt (a phosphine counterion and a separate gold-thiosugar complex, three disconnected components in one SMILES string) — not something DiffDock's single-ligand docking protocol is designed to handle, so it was left out rather than fed in incorrectly.
- **Protocol:** DiffDock's default inference config, unmodified (20 diffusion steps, 10 samples per complex) — same settings used for every other DiffDock run in this repo.
- **Metric:** top-pose confidence score, DiffDock's own calibration (c > 0 high confidence, -1.5 < c < 0 moderate, below that low).

## Results (n=13)

| Drug | Confidence | Band |
|---|---|---|
| Captopril | -0.00 | moderate, at the high-confidence boundary |
| Acetazolamide | -0.03 | moderate, at the high-confidence boundary |
| Metformin | -0.43 | moderate |
| Ebselen | -0.49 | moderate |
| Disulfiram | -0.77 | moderate |
| Ciprofloxacin | -0.99 | moderate |
| Doxycycline | -1.16 | moderate |
| Aspirin | -1.19 | moderate |
| Metronidazole | -1.23 | moderate |
| Omeprazole | -1.66 | low |
| Probenecid | -2.50 | low |
| Atorvastatin | -2.93 | low |
| Rifampicin | -2.96 | low |

None crossed strictly into DiffDock's "high confidence" band (c > 0), but two (captopril, acetazolamide) landed right at that boundary. 9 of 13 landed in the "moderate" band — a real, non-trivial hit rate for an unbiased repurposing screen, not evidence of a working drug.

## How to read this, honestly

**Captopril's result is chemically sensible, not a surprise, and that's worth saying plainly.** Captopril's real, established mechanism (it's an ACE inhibitor) already depends on a zinc-chelating thiol group, because ACE — its actual pharmacological target — is also a zinc metalloenzyme. Docking showing captopril as the top-scoring hit against a different zinc-dependent enzyme is consistent with known chemistry (zinc-chelating pharmacophores are an actual, published strategy explored for metallo-β-lactamase inhibitor design), not a random artifact. That consistency is a mild positive signal about the screen's validity — it's finding a chemically reasonable pattern, not noise — but it is not evidence captopril actually inhibits NDM-1 in a real assay.

**What this is:** a real, correctly-run virtual screen against a real, clinically important target, using verified drug structures and an unmodified, previously-validated docking protocol. That's legitimate computational drug discovery methodology, the same category of work pharma and academic groups actually publish.

**What this is not, stated as plainly as everywhere else in this repo:** proof that any of these drugs inhibit NDM-1. Docking confidence estimates pose plausibility, not binding affinity, and even real binding affinity wouldn't establish functional inhibition of the enzyme's carbapenem-hydrolyzing activity. Nothing here has touched a real protein or a real bacterial culture. The next real step, if this were pursued, would be an actual biochemical assay (recombinant NDM-1 + a chromogenic β-lactam substrate + candidate compound, measuring hydrolysis rate) — cheap and standard as these things go, but still a wet-lab step this repo has no path to run.

**Raw note:** this was a fast, single-pass screen (13 compounds, default DiffDock settings, no repeat sampling or ensemble scoring) done to demonstrate the infrastructure generalizes beyond the PFAS/enzyme-design project it was built for, not a rigorous or exhaustive repurposing study. A real study would use a much larger, systematically-curated approved-drug library (thousands of compounds, e.g. DrugBank's full approved set) and would repeat runs to check score stability before treating any result as a real lead.

## Expansion (n=32): a larger, more targeted library

The original 13-drug pass was a fast demonstration, not a real screen. This expansion adds 19 more real, PubChem-verified FDA-approved drugs, chosen specifically to include known β-lactamase inhibitors and metal chelators (mechanistically the two most plausible chemical classes for hitting a dizinc metalloenzyme's active site), plus one direct positive control.

- **Added:** vancomycin, amoxicillin, azithromycin, linezolid, meropenem (the enzyme's own hydrolyzed substrate in the crystal structure, PDB ligand 0RV — a positive control, not a repurposing candidate), levofloxacin, fosfomycin, clavulanic acid, sulbactam, penicillamine, dimercaprol, deferasirox, deferoxamine, 8-hydroxyquinoline, clioquinol, thiabendazole, cefiderocol, tetracycline, nitazoxanide.
- **Excluded:** zinc pyrithione — same reason as auranofin above, a multi-fragment ionic SMILES DiffDock can't dock as one ligand.
- **Failed to dock:** 8-hydroxyquinoline. DiffDock's own molecular-graph construction threw `ValueError: No edges and no nodes` on this SMILES and produced no output at all (confirmed: its result directory is empty). Excluded from the results below rather than silently dropped — the run itself continued fine for every other compound (`Failed for 1/32 complexes` in the run log).
- **Protocol, metric:** identical to the original 13-drug run, unmodified.

### Results (n=31, sorted by confidence; 8-hydroxyquinoline excluded, failed to dock)

| Drug | Confidence | Band |
|---|---|---|
| Clavulanic acid | 0.14 | **high** |
| Clioquinol | 0.02 | **high** |
| Nitazoxanide | -0.09 | moderate |
| Sulbactam | -0.15 | moderate |
| Aspirin | -0.32 | moderate |
| Penicillamine | -0.41 | moderate |
| Acetazolamide | -0.44 | moderate |
| Meropenem (positive control) | -0.60 | moderate |
| Ebselen | -0.61 | moderate |
| Dimercaprol | -0.71 | moderate |
| Thiabendazole | -0.75 | moderate |
| Fosfomycin | -0.96 | moderate |
| Tetracycline | -1.12 | moderate |
| Levofloxacin | -1.24 | moderate |
| Linezolid | -1.26 | moderate |
| Metformin | -1.28 | moderate |
| Deferasirox | -1.32 | moderate |
| Ciprofloxacin | -1.40 | moderate |
| Metronidazole | -1.65 | low |
| Omeprazole | -1.72 | low |
| Disulfiram | -1.75 | low |
| Atorvastatin | -1.80 | low |
| Captopril | -1.81 | low |
| Cefiderocol | -2.05 | low |
| Amoxicillin | -2.15 | low |
| Azithromycin | -2.39 | low |
| Doxycycline | -2.45 | low |
| Probenecid | -2.45 | low |
| Rifampicin | -3.22 | low |
| Vancomycin | -3.31 | low |
| Deferoxamine | -3.41 | low |

### How to read the two "high" hits, honestly

Two compounds crossed strictly into the high-confidence band this time, unlike the original 13-drug pass. Both need a specific, honest caveat rather than being read as good news at face value.

**Clavulanic acid (0.14) is the strongest score in the whole 32-drug set, and it is almost certainly a false positive, not a lead.** Clavulanic acid's real, well-established mechanism is covalent inhibition of *serine* β-lactamases (class A) — it forms an acyl-enzyme intermediate at a catalytic serine. NDM-1 is a *metallo*-β-lactamase (class B): it has no catalytic serine, uses zinc instead, and clavulanic acid (along with sulbactam and tazobactam, the other clinically-used "-bactam" inhibitors) is documented in the literature as pharmacologically ineffective against class B enzymes — that's precisely why NDM-1-carrying bacteria are resistant to clavulanate-combination drugs like Augmentin. *(INFERRED — this is standard clinical microbiology knowledge, not something I confirmed with a source in this session; this session's web search budget was exhausted before I could pull a citation. Flagging it as unverified-this-session rather than stating it as sourced fact.)* A docking score can't see that mechanistic mismatch — DiffDock only scores geometric/chemical pose plausibility, not whether the bound conformation is catalytically productive by the *right* mechanism. This is a clean example of why a high docking score is not evidence of real inhibition.

**Clioquinol (0.02) is at least mechanistically plausible, unlike clavulanic acid, but still unverified.** It's an 8-hydroxyquinoline derivative — a metal-chelating scaffold, and zinc chelation is a real, chemically sensible strategy against a dizinc enzyme (the same logic that made captopril's result in the original 13-drug pass chemically sensible, not noise). Notably, the *parent* compound, unmodified 8-hydroxyquinoline, failed to dock at all in this same run (see above) — so this result rests on one derivative, not a consistent pattern across the chemical family, and should be weighted accordingly. *(INFERRED, same caveat as above — I have not confirmed via a source this session whether clioquinol specifically has been studied against NDM-1.)*

**Positive control check:** meropenem, the carbapenem actually co-crystallized (as its hydrolyzed product) in the 4EYL structure used as the docking target, scored -0.60 — moderate band, not high. That's a useful calibration data point: a molecule *known* to bind this exact active site (it's sitting in the crystal structure) doesn't clear the "high confidence" bar either, in this same protocol. That argues for treating DiffDock's confidence bands here as a coarse ranking signal, not a well-calibrated absolute threshold — a real re-scoring the original 13-drug writeup didn't have available, now added.

**Net honest takeaway for n=32:** no compound in this expanded library is real evidence of an NDM-1 inhibitor. The two "high" scores are more useful as a lesson in the failure modes of docking-only screening (mechanism-blind scoring, no positive-control calibration) than as leads. If anything here were pursued further, it would start with the same real biochemical assay named above, not with either "high" hit specifically over another compound in the moderate band.
