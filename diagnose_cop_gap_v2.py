"""
diagnose_cop_gap_v2.py
======================
Evaluates designs through the SAME path as core/optimize.py's
AMRDesignProblem._evaluate (same T_cold, bed area, loss model, NTU mode,
particle diameter), so numbers are directly comparable to the optimizer's.

Why v1 (diagnose_cop_gap.py) overshoots: it never passed particle_diameter
or bed_cross_section_area, so it skipped the geometry-aware pumping/eddy
loss path that the optimizer always uses.

Run:  python diagnose_cop_gap_v2.py
"""
import numpy as np
from scipy.optimize import brentq

from core.mce_material import GADOLINIUM
from core.amr_cycle import AMRSystem
import core.optimize as opt

T_COLD = opt.T_COLD_K          # 291.0 K, as the optimizer uses
SPAN = opt.SPAN_K              # 10 K
BED = opt.BED_CROSS_SECTION_AREA_M2


def run_opt_path(H, f, mdot, mass, eps, bf, d_mm, material=GADOLINIUM):
    s = AMRSystem(material=material, mu0H_max=H, mass_regenerator=mass,
                  frequency=f, fluid_mdot=mdot, regenerator_effectiveness=eps,
                  loss_model=opt._LOSS_MODEL,
                  use_ntu_thermal_model=opt.USE_NTU_THERMAL_MODEL,
                  blow_fraction=bf, particle_diameter=d_mm / 1000.0,
                  bed_cross_section_area=BED)
    return s.run(T_COLD, SPAN)


def show(label, r):
    print(f"{label:34s} COP_elec={r.COP_electrical:7.3f}  Qc={r.Qc:9.1f} W  "
          f"W_mag={r.W_mag:7.1f}  W_parasitic={r.W_parasitic:7.1f}")


# Design in v1's "OPT" dict (also the 9.494 row in tests/test_design_recommendations.py)
D = dict(H=2.993, f=0.322, mdot=0.4999, mass=11.55, eps=0.83, bf=0.414)

print(f"Optimizer path: T_cold={T_COLD} K, span={SPAN} K, bed area={BED} m^2\n")
print("=== 1. Particle-diameter sweep on the v1 design ===")
for d in (0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0, 1.5, 2.0):
    show(f"d = {d:.2f} mm", run_opt_path(d_mm=d, **D))

print("\n=== 2. Which diameter reproduces COP 9.494? ===")
d_star = brentq(lambda d: run_opt_path(d_mm=d, **D).COP_electrical - 9.494, 0.1, 1.0)
r_star = run_opt_path(d_mm=d_star, **D)
show(f"d = {d_star:.3f} mm", r_star)
print(f"  COP matches 9.494 at d = {d_star:.3f} mm,")
print(f"  but Qc there is {r_star.Qc:.0f} W vs 14186 W stored with that design.")
print("  The stored 9.494 / 14186 W row lives in a SYNTHETIC test fixture")
print("  (tests/test_design_recommendations.py) with no particle diameter, so it")
print("  cannot be exactly reproduced from the current code.")

print("\n=== 3. Plan's knee design (1.11 T, 2.59 Hz, 0.49 kg/s, 5.31 kg, d=0.272 mm) ===")
K = dict(H=1.11, f=2.59, mdot=0.49, mass=5.31, eps=0.713, bf=0.414)
print("  (blow fraction not given in the plan; 0.414 assumed, the optimizer's usual value)")
show("knee, La-Fe-Si NOT used here (Gd)", run_opt_path(d_mm=0.272, **K))
try:
    from core.cascade import LAFESIH_FAMILY  # noqa: F401
    print("  Note: the plan's knee uses tuned La(Fe,Si)13Hy; this line uses Gd for a")
    print("  like-for-like path check only. Material swap is a separate step.")
except Exception:
    pass

print("\n=== Attribution (cumulative, optimizer path) ===")
print("  4.63  baseline (const loss 15%, const eps 0.85, 5 kg, 2 T, 2 Hz)")
print("  1.82  swap to state-dependent loss model        (0.39x)")
print("  2.03  eps from NTU instead of constant 0.85     (1.12x)")
print("  8.95  move to optimizer's H, f, mdot, mass      (4.41x)")
print("  10.43 apply blow fraction 0.414 (v1 script)     (1.17x)")
print(f"  {r_star.COP_electrical:.2f}  add particle diameter {d_star:.2f} mm + bed area (optimizer path)")
