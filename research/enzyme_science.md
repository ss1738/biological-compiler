# Enzyme Science Notes

What's actually verified this session, versus what's background context from the review papers found along the way. Kept separate on purpose.

## Fluoroacetate dehalogenase (FAcD): the target this pipeline actually uses

**Verified directly, not just cited:**

- PDB entry **1Y37**, organism *Burkholderia* sp. FA1, 1.50 Å resolution, homodimer, 304 residues/subunit, Mg²⁺ in the active site. EC 3.8.1.3.
- UniProt accession **Q1JU72**. Catalytic residues confirmed against the actual downloaded structure file, not just the UniProt annotation:
  - **Asp104**: nucleophile
  - **His271**: proton acceptor
  - **Asp128**: structural, required for activity
  - Binding-pocket residues: Arg105, Arg108, His149, Trp150, Tyr212
- No bound substrate ligand in 1Y37 (only water and Mg²⁺). That's why the design campaign used plain motif scaffolding instead of a substrate-contact potential; there was no ligand present to compute contacts against.
- Native substrate is fluoroacetate → glycolate: one C–F bond, activated by an adjacent carboxylate. This is mechanistically much simpler than a real PFAS molecule, which carries many C–F bonds along an otherwise chemically inert perfluorocarbon chain. FAcD is the best-characterized natural C–F bond-cleaving enzyme that's publicly available with a real structure. It is not a PFAS-degrading enzyme itself.

## rdhA (*Acidimicrobium* sp. strain A6): the actual PFAS-active lead, currently unusable

**Verified:** Jaffé et al. (2024) showed via gene-knockout experiments that the `rdhA` gene, a reductive dehalogenase, is required for real PFOA/PFOS defluorination in this organism. This is genuine, documented PFAS-degrading biology, not a proxy.

**Also verified:** as of this session there is no public structure or even a public sequence for this specific gene. Checked and came up empty in:
- UniProt (both narrow and organism-scoped queries)
- NCBI Protein database
- NCBI Assembly database (189 *Acidimicrobium* genus assemblies exist; none are strain A6)
- Full text of a 2026 review that discusses this exact gene

AlphaFold DB predictions are built from UniProt entries, so no UniProt entry means no AlphaFold model either.

**Bottom line:** rdhA is the real target. It just isn't usable for structure-based design yet. Worth rechecking periodically (see `mcp_setup.md` for how to keep tabs on this).

## Other enzyme families mentioned in the literature

Background only. Not verified in depth, not used in this pipeline. Pulled from abstracts of review papers found during the PFAS-engineering literature search. These are named as candidate families by the field, not things this project has worked with directly:

- **Haloacid dehalogenases**: the family FAcD belongs to. Explicitly named in the review literature as a relevant candidate family for PFAS-engineering work, which is part of why FAcD was chosen as this project's stand-in target.
- **Reductive dehalogenases**: the family rdhA belongs to.
- **Cytochrome P450s / monooxygenases**: named as candidates in multiple reviews. The mechanism would be oxidative rather than hydrolytic.
- **Peroxidases** (e.g. horseradish peroxidase) and **laccases**: reviewed specifically for PFAS degradation. "Laccase based per- and polyfluoroalkyl substances degradation: Status and future perspectives" (PMID 39637694) notes native laccases are slow and only partially effective without redox mediators.
- **CDO (cysteine dioxygenase)**: mentioned in the original brief for this document, not independently verified or researched this session. Flagging rather than writing anything definitive about it.

**Raw note:** this file reflects what came out of a real literature search done under real constraints. WebSearch quota was exhausted mid-session, so everything here came from PubMed/NCBI E-utilities and direct site fetches instead. It is not a comprehensive enzyme-science literature review. It's what surfaced while chasing one specific question, is there a real, structurally-usable PFAS enzyme, and it's honest about where that search actually reached versus where it stopped.
