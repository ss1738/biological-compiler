"""
ESMFold structure prediction + pass/fail filtering.

Thresholds (pLDDT >= 65, active-site RMSD <= 2.0A) were not chosen a priori —
they're the values used for the two real campaigns behind data/shortlist/, picked
because they're the standard "confident" pLDDT cutoff and a loose-but-meaningful
structural agreement bound. Loosening or tightening them changes what counts as
a "candidate"; there's nothing sacred about these exact numbers.

Known issue on the machine this was developed on: the torch/CUDA context has been
observed to hang on interpreter exit, leaving the model resident in GPU memory
long after the script finishes its work. Call os._exit(0) at the end of any script
that loads this model, rather than trusting normal shutdown.
"""
import torch
from transformers import AutoTokenizer, EsmForProteinFolding

PLDDT_PASS = 65.0
RMSD_PASS = 2.0


def load_model():
    tokenizer = AutoTokenizer.from_pretrained("facebook/esmfold_v1")
    model = EsmForProteinFolding.from_pretrained("facebook/esmfold_v1", low_cpu_mem_usage=True).cuda()
    model.esm = model.esm.half()
    model.trunk.set_chunk_size(64)
    model.eval()
    return tokenizer, model


def fold(tokenizer, model, sequence):
    """Returns (mean_plddt, pdb_string) for one sequence."""
    with torch.no_grad():
        inputs = tokenizer([sequence], return_tensors="pt", add_special_tokens=False)
        inputs = {k: v.cuda() for k, v in inputs.items()}
        out = model(**inputs)
    pl = out["plddt"][0]
    per_res = pl.mean(dim=-1) if pl.dim() == 2 else pl
    mean_plddt = per_res.mean().item() * (100 if per_res.max() <= 1.5 else 1)
    pdb_str = model.infer_pdb(sequence)
    return mean_plddt, pdb_str


def passes(mean_plddt, active_site_rmsd, plddt_thresh=PLDDT_PASS, rmsd_thresh=RMSD_PASS):
    return mean_plddt >= plddt_thresh and active_site_rmsd <= rmsd_thresh
