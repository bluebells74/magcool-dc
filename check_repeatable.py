"""
check_repeatable.py
===================
Runs the optimizer and the hysteresis A/B comparison several times with the
SAME seed, writing to a scratch folder (results/ is not touched), and
compares file hashes. Identical hashes = repeatable.

Run:  python check_repeatable.py            (quick, ~1-2 minutes)
      python check_repeatable.py --full     (real pop/gen sizes, slower)
"""
import hashlib
import os
import sys
import tempfile

from core.optimize import run_optimization
from core.hysteresis_sensitivity import run_hysteresis_sensitivity

FULL = "--full" in sys.argv
POP, GEN = (40, 25) if FULL else (16, 4)
N_RUNS = 3
scratch = tempfile.mkdtemp(prefix="repeat_check_")


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


print(f"pop_size={POP}, n_gen={GEN}, seed=1, runs={N_RUNS}, scratch={scratch}\n")

opt_hashes = []
for i in range(1, N_RUNS + 1):
    out = os.path.join(scratch, f"pareto_{i}.csv")
    run_optimization(pop_size=POP, n_gen=GEN, seed=1, out_csv=out,
                     per_material_out_dir=os.path.join(scratch, f"mat_{i}"))
    opt_hashes.append(sha(out))
    print(f"[optimizer] run {i}: {opt_hashes[-1]}", flush=True)

hys_hashes = []
for i in range(1, N_RUNS + 1):
    t = os.path.join(scratch, f"hys_{i}.txt")
    on = os.path.join(scratch, f"on_{i}.csv")
    off = os.path.join(scratch, f"off_{i}.csv")
    run_hysteresis_sensitivity(pop_size=POP, n_gen=GEN, seed=1, out_path=t,
                               out_csv_on=on, out_csv_off=off, verbose=False)
    hys_hashes.append((sha(t), sha(on), sha(off)))
    print(f"[hysteresis] run {i}: {hys_hashes[-1]}", flush=True)

print()
print("optimizer  :", "IDENTICAL" if len(set(opt_hashes)) == 1 else "DIFFERENT")
print("hysteresis :", "IDENTICAL" if len(set(hys_hashes)) == 1 else "DIFFERENT")
