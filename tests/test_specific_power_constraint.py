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


# ---- utilization-factor constraint (finish-plan addition) ----

def test_utilization_default_off_and_counts_constraints():
    assert AMRDesignProblem().n_constr == 0
    assert AMRDesignProblem(max_utilization=1.0).n_constr == 1
    assert AMRDesignProblem(max_specific_power_W_per_kg=1600.0, max_utilization=1.0).n_constr == 2


def test_utilization_constraint_sign_convention():
    x = np.array([2.0, 1.0, 0.2, 5.0, 0.8, 0.45, 0.5])
    out = {}
    AMRDesignProblem(max_utilization=1e6)._evaluate(x, out)
    assert out["G"][0] < 0          # huge cap never binds
    out = {}
    AMRDesignProblem(max_utilization=1e-6)._evaluate(x, out)
    assert out["G"][0] > 0          # tiny cap always violated


def test_both_constraints_produce_two_g_values():
    x = np.array([2.0, 1.0, 0.2, 5.0, 0.8, 0.45, 0.5])
    out = {}
    AMRDesignProblem(max_specific_power_W_per_kg=1600.0, max_utilization=1.0)._evaluate(x, out)
    assert len(out["G"]) == 2


def test_constrained_front_respects_utilization_limit():
    from core.thermal import regenerator_effectiveness
    rows = run_optimization_for_material(
        GADOLINIUM, "Gd", "Gd", pop_size=28, n_gen=8, seed=1, max_utilization=1.0)
    assert rows
    for r in rows:
        U = regenerator_effectiveness(
            r["mass_regenerator_kg"], r["frequency_Hz"], r["fluid_mdot_kgs"],
            particle_diameter=r["particle_diameter_mm"] / 1000.0,
            bed_cross_section_area=0.002)["U"]
        assert U <= 1.0 * 1.02   # rounding slack on CSV-rounded inputs
