"""Tests for the optional specific-power feasibility constraint in core/optimize.py."""
import numpy as np
from core.optimize import AMRDesignProblem, run_optimization_for_material
from core.mce_material import GADOLINIUM


def test_default_is_unconstrained():
    p = AMRDesignProblem()
    assert p.n_constr == 0
    assert p.max_specific_power_W_per_kg is None


def test_constraint_adds_one_constraint():
    p = AMRDesignProblem(max_specific_power_W_per_kg=1600.0)
    assert p.n_constr == 1


def test_constraint_sign_convention():
    """G <= 0 means feasible. A tiny-power design is feasible; a huge limit never binds."""
    x = np.array([2.0, 1.0, 0.2, 5.0, 0.8, 0.45, 0.5])
    out = {}
    AMRDesignProblem(max_specific_power_W_per_kg=1e9)._evaluate(x, out)
    assert out["G"][0] < 0
    out = {}
    AMRDesignProblem(max_specific_power_W_per_kg=1.0)._evaluate(x, out)
    assert out["G"][0] > 0


def test_constrained_front_respects_limit():
    limit = 1600.0
    rows = run_optimization_for_material(
        GADOLINIUM, "Gd", "Gd", pop_size=28, n_gen=8, seed=1,
        max_specific_power_W_per_kg=limit)
    assert rows
    for r in rows:
        # row values are rounded, allow 0.5% slack
        assert r["Qc_W"] / r["mass_regenerator_kg"] <= limit * 1.005
