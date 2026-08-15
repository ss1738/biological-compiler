"""
PFAS molecule reference data.

IMPORTANT — read this before assuming these are used anywhere: they aren't, yet.
Neither campaign behind data/shortlist/ used a substrate-contact potential, because
the RFdiffusion target structure (PDB 1Y37) has no bound ligand — only water and
Mg2+. So none of the 3,600 designs generated so far were guided toward, or checked
against, any of the molecules defined here. This module exists so a future run
that *does* have a substrate-bound structure (or that adds a docking/contact step)
has real, verified starting data instead of someone re-deriving SMILES strings
from memory under time pressure.

All values below verified against PubChem (pubchem.ncbi.nlm.nih.gov), not recalled.
"""

SUBSTRATES = {
    "PFOA": {
        "name": "perfluorooctanoic acid",
        "iupac_name": "2,2,3,3,4,4,5,5,6,6,7,7,8,8,8-pentadecafluorooctanoic acid",
        "smiles": "C(=O)(C(C(C(C(C(C(C(F)(F)F)(F)F)(F)F)(F)F)(F)F)(F)F)(F)F)O",
        "formula": "C8HF15O2",
        "molecular_weight": 414.07,
        "note": "one of the two PFAS compounds the EPA's 2024 drinking water rule sets a 4.0 ppt limit for",
    },
    "PFOS": {
        "name": "perfluorooctanesulfonic acid",
        "iupac_name": "1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,8-heptadecafluorooctane-1-sulfonic acid",
        "smiles": "C(C(C(C(C(F)(F)S(=O)(=O)O)(F)F)(F)F)(F)F)(C(C(C(F)(F)F)(F)F)(F)F)(F)F",
        "formula": "C8HF17O3S",
        "molecular_weight": 500.13,
        "note": "the other compound covered by the EPA's 4.0 ppt limit",
    },
    "fluoroacetate": {
        "name": "fluoroacetic acid",
        "iupac_name": "2-fluoroacetic acid",
        "smiles": "C(C(=O)O)F",
        "formula": "C2H3FO2",
        "molecular_weight": 78.04,
        "note": (
            "NOT a PFAS compound. This is the actual native substrate of fluoroacetate "
            "dehalogenase (PDB 1Y37), the enzyme this project's pipeline scaffolds "
            "against. One C-F bond next to a carboxylate — far simpler chemistry than "
            "a real PFAS chain. Included here because it's the molecule the current "
            "target structure's catalytic machinery actually evolved to process."
        ),
    },
}


def get(name):
    """Case-insensitive lookup, raises KeyError with the valid options if not found."""
    key = name.upper() if name.upper() in SUBSTRATES else name.lower()
    if key not in SUBSTRATES:
        raise KeyError(f"unknown substrate {name!r}; known: {list(SUBSTRATES)}")
    return SUBSTRATES[key]
