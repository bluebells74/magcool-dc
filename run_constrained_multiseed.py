"""
run_constrained_multiseed.py
============================
Phase 1, step 6 of the finish plan: rerun NSGA-III WITH the realism
constraints (specific power <= 1.6 kW/kg, utilization U <= 1.0) across
several seeds, so the headline numbers do not depend on one random start.

Writes (nothing in results/ is overwritten):
  results/constrained_multiseed/pareto_seed<N>.csv   one front per seed
  results/constrained_multiseed/summary.csv          one row per seed
  results/constrained_multiseed/summary.txt          mean / spread table

Run:  python run_constrained_multiseed.py
      python run_constrained_multiseed.py --seeds 1 2 3     (fewer seeds)
"""
import csv
import os
import statistics as st
import sys
import time

from core.optimize import run_optimization

MAX_SPECIFIC_POWER = 1600.0   # W per kg regenerator (best real device ~1.6 kW/kg)
MAX_UTILIZATION = 1.0         # judgment call, not a sourced number
OUT_DIR = os.path.join("results", "constrained_multiseed")

seeds = [1, 2, 3, 4, 5]
if "--seeds" in sys.argv:
    seeds = [int(s) for s in sys.argv[sys.argv.index("--seeds") + 1:]]

os.makedirs(OUT_DIR, exist_ok=True)


def knee(rows):
    """Balanced design: closest to the utopia point in normalized
    (COP up, cooling power up, cost down) space."""
    def norm(vals, hi_good):
        lo, hi = min(vals), max(vals)
        span = (hi - lo) or 1.0
        return [((v - lo) / span) if hi_good else ((hi - v) / span) for v in vals]
    c = norm([r["COP_electrical"] for r in rows], True)
    q = norm([r["Qc_W"] for r in rows], True)
    k = norm([r["cost_index_USD"] for r in rows], False)
    d = [((1 - a) ** 2 + (1 - b) ** 2 + (1 - e) ** 2) ** 0.5 for a, b, e in zip(c, q, k)]
    return rows[d.index(min(d))]


summary = []
for seed in seeds:
    t0 = time.time()
    out_csv = os.path.join(OUT_DIR, f"pareto_seed{seed}.csv")
    rows = run_optimization(
        seed=seed, out_csv=out_csv,
        per_material_out_dir=os.path.join(OUT_DIR, f"by_material_seed{seed}"),
        max_specific_power_W_per_kg=MAX_SPECIFIC_POWER,
        max_utilization=MAX_UTILIZATION)
    best = max(rows, key=lambda r: r["COP_electrical"])
    kn = knee(rows)
    summary.append(dict(
        seed=seed, n_designs=len(rows),
        best_COP=best["COP_electrical"], best_COP_Qc_W=best["Qc_W"],
        best_COP_mass_kg=best["mass_regenerator_kg"], best_COP_material=best["material"],
        knee_COP=kn["COP_electrical"], knee_Qc_W=kn["Qc_W"],
        knee_mass_kg=kn["mass_regenerator_kg"], knee_cost_USD=kn["cost_index_USD"],
        knee_material=kn["material"], seconds=round(time.time() - t0)))
    print(f"\n>>> seed {seed} done in {summary[-1]['seconds']} s: "
          f"best COP {best['COP_electrical']}, knee COP {kn['COP_electrical']}\n",
          flush=True)

with open(os.path.join(OUT_DIR, "summary.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(summary[0].keys()))
    w.writeheader()
    w.writerows(summary)


def ms(key):
    v = [s[key] for s in summary]
    sd = st.stdev(v) if len(v) > 1 else 0.0
    return st.mean(v), sd, min(v), max(v)


lines = [f"Constrained NSGA-III, seeds {seeds}",
         f"Limits: specific power <= {MAX_SPECIFIC_POWER:.0f} W/kg, utilization <= {MAX_UTILIZATION}",
         "(utilization cap of 1.0 is a judgment call, not a sourced number)", "",
         f"{'metric':22s} {'mean':>10s} {'stdev':>9s} {'min':>10s} {'max':>10s}"]
for key in ("n_designs", "best_COP", "best_COP_Qc_W", "best_COP_mass_kg",
            "knee_COP", "knee_Qc_W", "knee_mass_kg", "knee_cost_USD"):
    m, sd, lo, hi = ms(key)
    lines.append(f"{key:22s} {m:10.2f} {sd:9.2f} {lo:10.2f} {hi:10.2f}")
lines += ["", "Per seed:"] + [
    f"  seed {s['seed']}: best COP {s['best_COP']} ({s['best_COP_material']}), "
    f"knee COP {s['knee_COP']} / {s['knee_Qc_W']:.0f} W / {s['knee_mass_kg']} kg / "
    f"${s['knee_cost_USD']}" for s in summary]
text = "\n".join(lines)
with open(os.path.join(OUT_DIR, "summary.txt"), "w") as f:
    f.write(text + "\n")
print("\n" + text)
