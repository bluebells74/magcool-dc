# MagCool-DC: finish-plan status (Phase 0 and Phase 1)

Built on the original MagCool-DC code by Akhil (github.com/Akhil-025/magcool-dc).
All numbers below were reproduced on two machines (Windows and Linux) unless noted.

## What was done

| Item | Result |
|---|---|
| Frozen baseline | Tagged `v0.1-baseline`; all later work is on top of it |
| Test suite | 745 passed before changes, 749 after (4 new tests) |
| Repeatability | Optimizer and hysteresis comparison: 3 runs with the same seed gave identical files (small run size) |
| COP gap (4.63 vs 9.49) | Attributed to named factors, saved in `results/cop_gap_attribution.txt` |
| Realism limits on the optimizer | Specific power <= 1.6 kW/kg and utilization <= 1.0 (both optional, off by default) |
| Five-seed constrained run | `results/constrained_multiseed/summary.txt` |

## The COP gap, in one table

| Step | COP | Factor |
|---|---|---|
| Baseline (2 T, 2 Hz, 5 kg) | 4.63 | |
| State-dependent loss model | 1.82 | x0.39 |
| Effectiveness from NTU | 2.03 | x1.12 |
| Optimizer's field / frequency / flow / mass | 8.95 | x4.41 |
| Optimizer's blow fraction | 10.43 | x1.17 |
| Particle diameter and bed area (optimizer path) | 9.49 | x0.91 |

Most of the gap is the optimizer choosing a different design, not a modelling difference.

## Constrained optimizer, five seeds

- Best COP: 10.53 mean (10.35 to 10.59), always La(Fe,Si)13Hy.
- The knee (balanced) design is **not** stable across seeds: 4.6 to 14.1 kg and $3.2k to $8.5k. Report the range, not one design.
- The limits remove the unphysical cooling per kg, but the best COP stays about 10.5. The high COP is not explained by those two limits.

## Caveats (must travel with the numbers)

1. The 9.494 reference comes from a synthetic test fixture, not a saved optimizer run. Its cooling power (14,186 W) is not reproduced by the current code (12,779 W).
2. The particle diameter of 0.39 mm in the attribution is fitted to hit 9.494. It is not a recorded value.
3. The utilization cap of 1.0 is a judgment call, not a sourced number.
4. The optimizer's `regen_effectiveness` variable has no effect when the NTU model is on (checked directly). The value in the Pareto tables is not the effectiveness actually used.
5. Repeatability was checked at small run sizes only.
6. On one Windows PC, a security policy blocks a pandas file. That stops 3 test files (72 tests) from loading and fails 4 more. Result on that PC: 673 passed, 4 failed, 3 collection errors, all from the pandas block. The full suite passed 749/749 on the same PC earlier in the project, before the block appeared. The full suite passes on GitHub Actions (Python 3.11 and 3.12, Ubuntu): all green on the fork’s main.

## Not done yet

- Validation dataset: 3 real devices now, the plan needs 30 or more.
- 1-D regenerator model: errors of -83%, +105% and -63% against 3 devices, unexplained.
- Bayesian calibration with error bars, and a held-out test set.
- Year-long data-center simulation, probability of beating compressors, and the required-improvement targets.
- Bill of materials rework (the constrained designs cost very differently from the old knee).

Papers A and B depend on the items above, so neither is close to submittable yet.
