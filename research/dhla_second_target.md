# A Second Target: Haloalkane Dehalogenase (DhlA)

Everything documented elsewhere in this repo scaffolds fluoroacetate dehalogenase (FAcD, a haloacid dehalogenase). This is a real, independent test of a different candidate family named in the same PFAS-engineering review literature: haloalkane dehalogenases. Run overnight, unattended, using the exact same validated pipeline pointed at a new target.

## The hypothesis, stated honestly before results

FAcD's native substrate is fluoroacetate, one activated C-F bond next to a carboxylate. Real PFAS chains carry many C-F bonds on an otherwise chemically inert perfluorocarbon backbone. Haloalkane dehalogenases process a mechanistically different substrate class: unactivated alkyl halides, held in a buried hydrophobic pocket, no adjacent activating group. That's structurally closer to what a PFAS chain actually looks like than FAcD's substrate is. The real, falsifiable question: does a haloalkane-dehalogenase-based design show any better docking affinity for real PFAS substrates than the FAcD-based designs did (which scored 0/30 high-confidence for both PFOA and PFOS)?

## The target

**DhlA**, haloalkane dehalogenase from *Xanthobacter autotrophicus*, PDB **2HAD**, 1.90 Å resolution, EC 3.8.1.5. Catalytic triad verified directly against the downloaded structure file (not just the summary): **Asp124** (nucleophile), **Asp260** (H-bond acceptor), **His289** (H-bond intermediary). No bound ligand in this structure (only water), same situation as FAcD's 1Y37 — plain motif scaffolding, no substrate-contact potential.

Real native substrate: 1,2-dichloroethane, SMILES `C(CCl)Cl`, verified via PubChem.

## Pre-flight check, before committing the full run

A 2-backbone sanity check came back 0/18 passing candidates — concerning on its own, but too small a sample to draw a conclusion from. A 10-backbone follow-up came back **30/90 passing (33%)**, comparable to or better than FAcD's own pass rate. That resolved the concern: the earlier 0/18 was small-sample noise, not a real problem with the target or the contig design. Proceeded to the full run on that basis.

## Full results (200 backbones, unattended, ~4.5 hours total)

| Stage | Result |
|---|---|
| Generation | 200 backbones → 1,800 sequences → 474 candidates passed (26.3%) |
| Curation | 30-candidate shortlist, capped 3/backbone (19 distinct backbones contributing) |
| OpenMM MD (100ps) | 28/30 stable (backbone drift < 2.0 Å), 22/30 tight active site (< 1.0 Å) |
| Chai-1 (independent fold) | **30/30 confident**, pTM mean 0.879, range matches FAcD's own 30/30 result almost exactly |
| DiffDock — 1,2-dichloroethane (native substrate) | mean confidence -0.68, **0/30 high-confidence** |
| DiffDock — PFOA | mean confidence -1.97, **0/30 high-confidence** |
| DiffDock — PFOS | mean confidence -2.20, **0/30 high-confidence** |

Full data in `data/dhla_shortlist/`: manifest, relaxed structures, DiffDock results, Chai-1 results, and the complete campaign log.

## How to read this, honestly

This is not the result the hypothesis predicted, but it's also not a clean answer to the hypothesis either — and that distinction matters. Compare to FAcD: there, the *native* substrate (fluoroacetate) docked at high confidence in 9/30 candidates, which validated that the scaffolding method was building a real, substrate-selective pocket before the PFAS cross-test showed that pocket didn't fit PFAS. Here, DhlA's own native substrate — the thing its real catalytic triad actually evolved to process — **also scored 0/30 high-confidence**. That's a different failure mode than "wrong substrate for a real pocket." It's closer to "no real functional pocket formed" for this specific scaffold.

The most likely explanation: DhlA's real mechanism depends on a buried hydrophobic tunnel, not just three catalytic residues sitting in open space. FAcD's binding pocket is also shaped by non-catalytic residues (Arg105, Arg108, His149, Trp150, Tyr212 — documented in `enzyme_science.md`) that weren't included in either campaign's scaffolding, but FAcD's chemistry may be more forgiving of that omission than DhlA's buried-tunnel architecture is. Chai-1's 30/30 confident result shows the sequences still fold into well-defined structures — so the failure isn't "these are bad proteins," it's specifically that this motif-only scaffolding recipe didn't reconstruct a working substrate pocket for this target.

**The original hypothesis — does a haloalkane-dehalogenase-family target dock PFAS any better than FAcD — remains genuinely untested by this data.** Not because the result was negative, but because the negative control (does it even bind its own substrate) also failed, which means this run can't distinguish "haloalkane dehalogenases are a worse PFAS starting point" from "this particular 3-residue scaffold wasn't enough for this particular protein's mechanism." A real next test of the actual hypothesis would need to include DhlA's binding-pocket residues in the scaffold, not just the catalytic triad, the same way FAcD's design could be extended the same way.

**Raw note:** this cost about 4.5 hours of otherwise-idle GPU time, not the full night it was expected to take. Real result either way, real new data, genuinely inconclusive on the question it was built to answer — worth stating plainly rather than either overselling the negative result or hiding that the test came back ambiguous.
