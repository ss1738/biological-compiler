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
