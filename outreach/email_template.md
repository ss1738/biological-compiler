# Outreach Email Template

Written honestly — no fabricated backstory, no overselling. Fill in `[bracketed]` parts per recipient. Read `pi_shortlist.md` for who this is meant for and why.

---

**Subject:** AI-designed enzyme candidates for C–F bond cleavage — looking for a fluoride-assay collaboration

Hi Professor [Name],

I've been building a computational pipeline for enzyme design (RFdiffusion → ProteinMPNN → ESMFold) and used it to generate candidates around the catalytic site of fluoroacetate dehalogenase — I'm reaching out because [your work on rdhA-driven PFAS defluorination / your fluoride-assay screening method / your work on in-silico PFAS enzyme design] is the closest match I could find to what I'd actually need to test this.

To be upfront about what this is and isn't: the pipeline scaffolds new protein backbones around FAcD's real catalytic triad (Asp104/Asp128/His271, from PDB 1Y37), designs sequences for those backbones, and checks with an independent structure-prediction model (ESMFold) whether each sequence actually folds back into the intended shape. Out of 3,600 sequences generated across two runs, I have 30 candidates where that self-consistency check comes back strong — active-site RMSD under 0.75 Å, pLDDT 70–84.

That's a real signal, but it's not evidence of activity. Nothing has been synthesized or tested. FAcD's native substrate is a single C–F bond next to a carboxylate — simpler chemistry than an actual PFAS molecule — so even a candidate that works exactly as designed wouldn't be a PFAS-degrading enzyme without further work. I'm not claiming otherwise.

What I'm asking: would you be open to expressing 5–10 of these sequences cell-free and running them through a fluoride-release assay? I can send the full sequence/structure set, the generation and filtering methodology, and iterate on the design if the first batch tells you something useful. Happy to talk about authorship/IP terms upfront — I'd want you to own the assay data, and I'm not looking to extract free labor without a real collaboration.

If this isn't a fit for your lab right now, I'd still appreciate knowing whether the approach itself seems worth pursuing, or if there's an obvious flaw I'm not seeing.

Sequences and structures attached / linked here: [repo link]

Thanks for reading this far,
[Your name]

---

**Raw note:** sent to Peter Jaffé and Lawrence Wackett on 2026-08-15, personalized per recipient. Don't know yet if either will land. It's honest about the self-consistency-only nature of the results because that's the actual state of things — softening that to sound more impressive would just create a worse first conversation once someone with real domain expertise looks closely.
