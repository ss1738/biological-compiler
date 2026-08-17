# De Novo Binder Design Against NDM-1

A fundamentally different method from everything else in this repo. Every other campaign here scaffolds a new enzyme around a fixed catalytic site. This one asks a different question: can a brand-new protein be designed, from nothing, to physically bind a real disease target? Same target as the repurposing screen (`research/ndm1_drug_repurposing.md`) — NDM-1, PDB 4EYL — but a completely different design method: RFdiffusion's protein-protein-interaction (binder) mode, not motif scaffolding.

## Method

- **Target:** NDM-1, PDB 4EYL, chain A, residues 42–272 (231 residues). Residue numbering does not start at 1 — verified directly against the structure file, a real bug caught during setup (`AssertionError: ('A', 1) is not in pdb file!`).
- **Hotspots:** His120, Asp124, His250 — real, UniProt-verified zinc-coordinating residues spanning both of NDM-1's catalytic zinc sites, given to RFdiffusion via `ppi.hotspot_res`.
- **Generation:** RFdiffusion binder mode, contig `[A42-272/0 60-100]`, one binder backbone per run, 150 backbones generated.
- **Sequence design:** ProteinMPNN, chain B (the binder) only — chain A (the target) held completely fixed via `assign_fixed_chains.py --chain_list B`, so the target sequence can never be mutated. 4 sequences per backbone, sampling temperature 0.2. 600 sequences total.
- **Scoring:** Chai-1 (AlphaFold3-class) folds the full two-chain complex for every sequence, and ipTM (interface predicted TM-score, the metric that specifically measures whether the two chains are predicted to interact, not just whether each folds well individually) is extracted from `scores.model_idx_0.npz`.
- **Orchestration:** each stage runs as its own process (the same CUDA-teardown `os._exit(0)` workaround used everywhere in this repo), auto-chained overnight with a wrapper script that watches for stage 1's process to exit before launching stage 2 — no manual intervention needed between stages.

## Headline results (n=600)

| | |
|---|---|
| Sequences folded | 600 / 600 (0 failures) |
| Mean ipTM | 0.446 |
| Max ipTM | 0.901 |
| Min ipTM | 0.114 |
| n with ipTM > 0.5 | 255 |
| n with ipTM > 0.8 | 66 |

A raw 42.5% pass rate at ipTM > 0.5 is high — high enough that it demanded real scrutiny before being treated as a result, not just reported at face value.

## Testing my own hypothesis, and being wrong about it

The first candidates back had a real, visible problem: the designed sequences are dominated by 2–3 amino acids, mostly alanine (sampled sequences ran 28–81% top-3-residue content, often 30–58% alanine alone — see raw sequences in `data/ndm1_binder_campaign/binder_seqs.jsonl`). Low-complexity, alanine-heavy sequences are a real, documented failure mode in protein design: AlphaFold-family structure predictors (Chai-1 included) tend to fold idealized, simple helical bundles with artificially inflated confidence, independent of whether the sequence is a good real binder. That's a real, mechanistically specific reason to suspect the whole 255-candidate count was inflated by this exact artifact.

**I tested that hypothesis properly instead of asserting it.** Across all 600 sequences, I computed Shannon entropy and alanine fraction per sequence and correlated both against ipTM:

| ipTM band | n | mean entropy (bits) | mean alanine fraction |
|---|---|---|---|
| > 0.8 | 66 | 2.902 | 0.427 |
| 0.5–0.8 | 189 | 2.893 | 0.428 |
| ≤ 0.5 | 345 | 2.756 | 0.455 |

Pearson r (ipTM vs. entropy) = **+0.20**. Pearson r (ipTM vs. alanine fraction) = **−0.14**. Both weak, and both in the *opposite* direction from what the low-complexity-artifact hypothesis predicted — if anything, the higher-scoring sequences are very slightly *more* diverse, not less. **The hypothesis is not supported by the full data.** It looked right from an 8-sequence sample; it doesn't hold at n=600. That's worth stating plainly rather than quietly dropping — this is the same standard applied to every other claim in this repo.

What *is* still real and worth flagging: composition across the **entire population**, regardless of score, is unusually low-diversity compared to natural proteins (mean entropy ~2.8 bits vs. roughly 4.0–4.2 for typical natural sequences; mean alanine content ~43% vs. a natural background of roughly 8% — *INFERRED baseline, not verified via a source this session, this session's web search budget was exhausted*). That's a real, uniform design-quality concern, most likely caused by `denoiser.noise_scale_ca=0 denoiser.noise_scale_frame=0` in the generation script — settings inherited from the enzyme-scaffolding pipeline, where zero noise is correct for precisely preserving fixed catalytic-residue geometry, but likely over-idealizes backbones for de novo binder generation. That's INFERRED, not proven — no controlled ablation was run. It just doesn't explain the score distribution the way I first thought.

## A real, independent structural check: does the binder actually reach the hotspot?

ipTM alone doesn't confirm a candidate is doing anything at the intended catalytic zinc-binding site — it's a global interface-confidence number, not a location check. So a second, independent, purely geometric verification was run: for every one of the 255 ipTM>0.5 candidates, minimum atomic distance was computed between the binder chain and the real hotspot residues (His120/Asp124/His250, correctly re-indexed from the original PDB numbering, 42–272, to Chai-1's own sequential 1–231 renumbering — the exact same offset bug caught earlier in this campaign, re-checked here rather than assumed fixed).

**Result: 116 / 255 candidates place the binder within 5 Å of the real hotspot region**, with the closest contacts at 1.7–2.8 Å — genuinely tight, physically real contact distances, not a coincidental global fold. This is independent evidence that RFdiffusion's hotspot-guided generation is doing its actual job geometrically, on top of (not explained by) Chai-1's own confidence score.

**The double-filtered shortlist — ipTM > 0.5 AND real hotspot contact < 5 Å — is 116 candidates.** This is the number that should be treated as the campaign's real output, not the raw 255. Top 20 by ipTM, all hotspot-verified:

| Candidate | ipTM | Hotspot contact (Å) | Length |
|---|---|---|---|
| binder_0060_seq3 | 0.901 | 4.53 | 61 |
| binder_0135_seq1 | 0.882 | 3.65 | 91 |
| binder_0098_seq1 | 0.877 | 3.48 | 88 |
| binder_0098_seq0 | 0.875 | 3.56 | 88 |
| binder_0054_seq1 | 0.873 | 4.88 | 98 |
| binder_0135_seq0 | 0.865 | 2.78 | 91 |
| binder_0025_seq0 | 0.862 | 2.54 | 97 |
| binder_0021_seq2 | 0.862 | 3.60 | 79 |
| binder_0075_seq3 | 0.853 | 3.43 | 82 |
| binder_0025_seq3 | 0.843 | 3.19 | 97 |

Full 116-candidate list, structures, sequences, and raw scores in `data/ndm1_binder_campaign/`.

## How to read this, honestly

**What this is:** a real, complete, unattended overnight run of a legitimate de novo binder-design method (RFdiffusion PPI mode → ProteinMPNN → Chai-1 interface scoring) against a real, clinically important target, with two independent computational filters (interface confidence and geometric hotspot contact) instead of one, and an honest correction of my own first hypothesis when the full-data check didn't support it.

**What this is not:** evidence that any of these sequences actually bind NDM-1 in reality. Every caveat that applies to the rest of this repo applies here, more so — nothing has been synthesized, expressed, or tested against real protein.

## Closing the gap: does the binder actually match what RFdiffusion designed?

The write-up above originally flagged a real missing check: ipTM confirms the two chains are predicted to interact, and the hotspot-contact check confirms *where*, but neither confirms the binder's predicted fold matches what RFdiffusion actually designed rather than something Chai-1 independently converged on. That's the same self-consistency question the enzyme-scaffolding pipeline elsewhere in this repo always asks (ESMFold RMSD vs. the RFdiffusion backbone) — so it was run here too, on all 116 hotspot-verified candidates: align the original RFdiffusion backbone and the Chai-1 predicted complex on the target chain, then measure CA RMSD of the binder chain in that shared frame.

**First attempt at this hit the exact same residue-numbering bug this campaign had already been caught twice before** — the original RFdiffusion PDB keeps the real 42–272 numbering for the target chain, Chai-1's output renumbers it 1–231, and naively intersecting the two numbering schemes produced a garbage alignment (a suspiciously identical "190 aligned atoms" on every single comparison — the coincidental integer overlap between {42..272} and {1..231}, not real correspondence). That gave a nonsense result (mean RMSD 19.55 Å, 0/116 under 5 Å) that would have been a real false negative if reported. Caught before writing it up, by noticing the too-uniform atom count; fixed with the same −41 offset used earlier for the hotspot check; reran with a sanity assertion (`len(common_A) > 220`) to stop this class of bug from silently recurring.

**Corrected result:**

| | |
|---|---|
| n analyzed | 116 |
| Mean RMSD | 4.00 Å |
| Median RMSD | 2.42 Å |
| n with RMSD < 2.0 Å | 48 |
| n with RMSD < 5.0 Å | 102 |
| n with RMSD < 10.0 Å | 107 |
| n with RMSD > 15.0 Å | 7 |

**The real, triple-verified result of this campaign is 48 candidates** — ipTM > 0.5 AND real hotspot contact < 5 Å AND backbone self-consistency RMSD < 2.0 Å (the same self-consistency bar used for the FAcD/DhlA enzyme campaigns elsewhere in this repo). Top 10, all three checks passed:

| Candidate | ipTM | Hotspot contact (Å) | Backbone RMSD (Å) |
|---|---|---|---|
| binder_0060_seq3 | 0.901 | 4.53 | 0.68 |
| binder_0135_seq1 | 0.882 | 3.65 | 0.93 |
| binder_0098_seq1 | 0.877 | 3.48 | 1.22 |
| binder_0098_seq0 | 0.875 | 3.56 | 0.89 |
| binder_0054_seq1 | 0.873 | 4.88 | 1.66 |
| binder_0135_seq0 | 0.865 | 2.78 | 1.30 |
| binder_0021_seq2 | 0.862 | 3.60 | 1.20 |
| binder_0025_seq0 | 0.862 | 2.54 | 1.69 |
| binder_0075_seq3 | 0.853 | 3.43 | 1.81 |
| binder_0075_seq1 | 0.842 | 3.96 | 1.98 |

Full 48-candidate list and structures in `data/ndm1_binder_campaign/final_verified/`.

**What's still real and unresolved:** the sequence composition problem. Even this 48-candidate final shortlist is drawn from the same low-diversity, alanine-heavy sequence population as the rest of the campaign (see the entropy/composition analysis above — that concern was about whether composition explains *which* candidates score well, which it doesn't; it says nothing about whether the composition itself is a real design-quality problem, which it still is). A real next step, if pursued, would rerun generation with nonzero backbone noise as a controlled comparison before trusting these specific sequences over the discarded ones.

The real next step, same as everywhere else in this repo: an actual binding assay (recombinant NDM-1 + a labeled or competitive binding assay against a shortlisted candidate), not more computation. Nothing here substitutes for that. But this is now a meaningfully stronger computational result than the raw ipTM number alone suggested — three independent checks, not one, and the two mistakes made while getting here (the retracted composition hypothesis, the numbering bug in this exact section) are documented rather than quietly fixed and hidden.
