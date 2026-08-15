"""
Kabsch-aligned CA RMSD between a predicted structure and its reference backbone,
with a separate active-site-only RMSD after global alignment.

This is the actual method used to score all 3,600 sequences across both campaigns
behind data/shortlist/ — not a simplified stand-in.
"""
import numpy as np


def parse_ca(path):
    coords = {}
    with open(path) as f:
        for line in f:
            if line.startswith("ATOM") and line[12:16].strip() == "CA":
                resnum = int(line[22:26])
                x, y, z = float(line[30:38]), float(line[38:46]), float(line[46:54])
                coords[resnum] = np.array([x, y, z])
    return coords


def kabsch(P, Q):
    """Rotates+translates P onto Q (least-squares). Returns aligned P."""
    Pc, Qc = P - P.mean(0), Q - Q.mean(0)
    H = Pc.T @ Qc
    U, S, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    D = np.diag([1, 1, d])
    R = Vt.T @ D @ U.T
    return (R @ Pc.T).T + Q.mean(0)


def active_site_rmsd(reference_pdb, predicted_pdb, motif_positions):
    """
    Aligns predicted_pdb onto reference_pdb globally (all CA atoms), then measures
    RMSD restricted to motif_positions (1-indexed residue numbers) after that
    alignment. Raises if the two structures don't have matching residue numbering
    — that's a real failure mode (e.g. ESMFold dropping/adding a residue), not
    something to silently paper over.
    """
    ref = parse_ca(reference_pdb)
    pred = parse_ca(predicted_pdb)
    ref_resnums = sorted(ref.keys())
    pred_resnums = sorted(pred.keys())
    if pred_resnums != ref_resnums:
        raise ValueError(f"residue mismatch: {reference_pdb} vs {predicted_pdb}")

    ref_coords = np.array([ref[r] for r in ref_resnums])
    pred_coords = np.array([pred[r] for r in pred_resnums])
    pred_aligned = kabsch(pred_coords, ref_coords)

    backbone_rmsd = float(np.sqrt(np.mean(np.sum((pred_aligned - ref_coords) ** 2, axis=1))))

    idx = [ref_resnums.index(p) for p in motif_positions]
    site_rmsd = float(np.sqrt(np.mean(np.sum((pred_aligned[idx] - ref_coords[idx]) ** 2, axis=1))))

    return dict(backbone_rmsd=backbone_rmsd, active_site_rmsd=site_rmsd)
