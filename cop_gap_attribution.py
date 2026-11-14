"""
cop_gap_attribution.py
======================
Phase 1 "done when" item: ONE saved table attributing the COP gap between the
stage-4 baseline (4.63) and the NSGA-III design (9.494) to named factors.

Every step changes one thing and re-runs the same AMRSystem code path. The
last step uses the optimizer's own evaluation path (particle diameter, bed
area, T_cold = 291.0 K). The 0.39 mm particle diameter is NOT a recorded
optimizer value: the 9.494 row exists only in a synthetic test fixture with
no diameter, so 0.39 mm is the value that reproduces 9.494 under the current
code (a fitted value, flagged as such in the output).

Writes: results/cop_gap_attribution.txt
Run:    python cop_gap_attribution.py
"""
import os

from scipy.optimize import brentq

import core.optimize as opt
from core.amr_cycle import AMRSystem
from core.loss_model import StateDependentLossModel
from core.mce_material import GADOLINIUM

SPAN = 10.0
LOSS = StateDependentLossModel()
BASE = dict(mu0H_max=2.0, mass_regenerator=5.0, frequency=2.0,
            fluid_mdot=0.08, regenerator_effectiveness=0.85)
OPTD = dict(mu0H_max=2.993, mass_regenerator=11.55, frequency=0.322,
            fluid_mdot=0.4999, regenerator_effectiveness=0.83)
TARGET = 9.494


def run(params, T_cold, loss=None, ntu=False, bf=0.5, d_mm=None):
    kw = dict(material=GADOLINIUM, loss_model=loss, use_ntu_thermal_model=ntu,
              blow_fraction=bf, **params)
    if d_mm is not None:
        kw.update(particle_diameter=d_mm / 1000.0,
                  bed_cross_section_area=opt.BED_CROSS_SECTION_AREA_M2)
    return AMRSystem(**kw).run(T_cold, SPAN)


T_STAGE4 = 291.15
steps = []
steps.append(("Baseline: 2 T, 2 Hz, 5 kg, 0.08 kg/s, const eps 0.85, const 15% loss",
              run(BASE, T_STAGE4)))
steps.append(("+ state-dependent loss model",
              run(BASE, T_STAGE4, loss=LOSS)))
steps.append(("+ effectiveness from NTU (not constant)",
              run(BASE, T_STAGE4, loss=LOSS, ntu=True)))
steps.append(("+ optimizer's field/frequency/flow/mass (2.993 T, 0.322 Hz, 0.4999 kg/s, 11.55 kg)",
              run(OPTD, T_STAGE4, loss=LOSS, ntu=True)))
steps.append(("+ optimizer's blow fraction 0.414",
              run(OPTD, T_STAGE4, loss=LOSS, ntu=True, bf=0.414)))
steps.append(("+ optimizer's T_cold 291.0 K (vs 291.15 K)",
              run(OPTD, opt.T_COLD_K, loss=LOSS, ntu=True, bf=0.414)))

d_star = brentq(lambda d: run(OPTD, opt.T_COLD_K, loss=LOSS, ntu=True, bf=0.414,
                              d_mm=d).COP_electrical - TARGET, 0.1, 1.0)
steps.append((f"+ particle diameter {d_star:.3f} mm and bed area {opt.BED_CROSS_SECTION_AREA_M2} m^2 "
              f"(optimizer path; FITTED diameter)",
              run(OPTD, opt.T_COLD_K, loss=LOSS, ntu=True, bf=0.414, d_mm=d_star)))

lines = ["COP gap attribution, Gd regenerator, 10 K span",
         "Each row changes one factor on top of the row above.", "",
         f"{'step':92s} {'COP_elec':>9s} {'x prev':>7s} {'Qc [W]':>9s}"]
prev = None
for label, r in steps:
    mult = "" if prev is None else f"{r.COP_electrical / prev:.2f}"
    lines.append(f"{label[:92]:92s} {r.COP_electrical:9.3f} {mult:>7s} {r.Qc:9.1f}")
    prev = r.COP_electrical
first, last = steps[0][1], steps[-1][1]
lines += ["",
          f"Total: {first.COP_electrical:.3f} -> {last.COP_electrical:.3f} "
          f"= {last.COP_electrical / first.COP_electrical:.2f}x "
          f"(NSGA-III reported {TARGET} = {TARGET / first.COP_electrical:.2f}x)",
          "",
          "Caveats:",
          f"  - {TARGET} comes from a synthetic test fixture (tests/test_design_recommendations.py)",
          "    with Qc = 14186 W and no particle diameter. Under the current code the",
          f"    matching design delivers Qc = {last.Qc:.0f} W, so the cooling power does NOT reproduce.",
          f"  - The diameter {d_star:.3f} mm is fitted to hit {TARGET}, not a recorded optimizer value.",
          "  - Most of the gap (the 'move to optimizer design point' step) is simply that the",
          "    optimizer runs a different design (bigger field, lower frequency, more mass),",
          "    not a modelling difference."]
text = "\n".join(lines)
os.makedirs("results", exist_ok=True)
with open(os.path.join("results", "cop_gap_attribution.txt"), "w") as f:
    f.write(text + "\n")
print(text)
print("\nWrote results/cop_gap_attribution.txt")
