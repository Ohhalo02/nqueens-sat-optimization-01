# N-Queens SAT Encodings and Exact Solvers

Single-author course project comparing five at-most-one (AMO) CNF encodings—pairwise, binary, commander, sequential counter, and product—with CBC, Gurobi, CPLEX MIP, OR-Tools CP-SAT, and CPLEX CP Optimizer on the empty-board N-Queens feasibility problem. The manuscript uses Elsevier's `cas-sc` class.

The historical benchmark is [`nqueens_sat/results/benchmark_results.csv`](nqueens_sat/results/benchmark_results.csv). It contains 116 aggregate rows across 13 board sizes from N=4 to N=200. Coverage is uneven: only Binary among the SAT encodings has archived measurements at N=150 and N=200. Missing rows are not timeouts. Raw repetitions, exact collection versions, and a complete hardware record were not preserved, so the archived figures support descriptive comparisons only. The CSV's `total_time` is formula/model construction plus solver invocation, excluding solution extraction and process startup. This is not end-to-end latency.

## Install

Use Python 3.10 or newer. `requirements.txt` installs PySAT, PuLP/CBC, OR-Tools, Pandas, NumPy, Matplotlib, and Seaborn. Gurobi and IBM CPLEX/CP Optimizer are optional commercial dependencies; their Python packages and suitable licenses must be installed separately to reproduce those rows. Community license size limits can prevent larger cases.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Validate and benchmark

```powershell
python nqueens_sat/test_validation.py
python nqueens_sat/run_benchmark.py --solvers BinaryEncoder ILP-Gurobi CP-SAT-ORTools --sizes 20 50 100 150 200 --repeats 3 --wall-limit 120
```

The validator asserts SAT/UNSAT and solution validity on small boards for all five encodings plus CBC and CP-SAT. The runner launches each case in a separate process and enforces a full-process wall deadline. It writes `raw.csv`, `summary.csv`, and `metadata.json` in a new timestamped directory under `nqueens_sat/results/runs/`; the historical CSV is never overwritten. The summary uses a median only when all requested repetitions finish with the same SAT/UNSAT status. Each solver is configured for one worker where the Python API allows it. `total_time` retains the historical construction-plus-solver-call definition; `wall_total` includes solution extraction inside the worker, and `process_wall_time` also includes startup and validation. These measures answer different questions and should not be mixed in a plot.

The benchmark's CLI also accepts `--output PATH`. The default full matrix includes large pairwise formulas and can require substantial RAM and runtime; select methods and sizes appropriate to the machine. New run data are separate from, and should not be silently merged with, the historical dataset.

The manuscript's controlled protocol check is in `nqueens_sat/results/benchmarks/new_benchmark/`: 45 successful, validated repetitions for Binary/Glucose4, Gurobi, and CP-SAT at N=20, 50, 100, 150, and 200. Its median CP-SAT result at N=200 differs from the archived value, so the report presents the two datasets separately. The recorded source working tree was modified during collection; the run is not pinned to a clean commit.

The clean-source large-board comparison is in `nqueens_sat/results/benchmarks/large_n_benchmark/`: 48 repetitions for all five SAT encodings, CBC, Gurobi, and CP-SAT at N=150 and 200. It was run with no local source changes, three repetitions per cell, one worker, and a 120-second full-process deadline. The public metadata records a SHA-256 fingerprint of the Python source files used by both clean-source runs. Sequential and CBC timed out in all three N=200 repetitions; no completion time is reported for either cell. To repeat this protocol, run:

```powershell
python nqueens_sat/run_benchmark.py --solvers BinomialEncoder BinaryEncoder CommanderEncoder SequentialEncoder ProductEncoder ILP-PuLP-CBC ILP-Gurobi CP-SAT-ORTools --sizes 150 200 --repeats 3 --wall-limit 120
```

The companion clean-source smaller-board comparison is in `nqueens_sat/results/benchmarks/common_small_benchmark/`: 72 repetitions for the same eight methods at N=20, 50, and 100. No Python source changed between the two clean-source runs. CBC timed out in all three N=20 runs despite completing its N=50 and N=100 runs. The two clean runs share the same worker count, deadline, and timing definitions, while their raw data and metadata remain separate.

```powershell
python nqueens_sat/run_benchmark.py --solvers BinomialEncoder BinaryEncoder CommanderEncoder SequentialEncoder ProductEncoder ILP-PuLP-CBC ILP-Gurobi CP-SAT-ORTools --sizes 20 50 100 --repeats 3 --wall-limit 120
```

The historical archive, the earlier protocol check, and the two clean runs have different provenance and are not pooled. Every successful placement in the new runner is validated before it is recorded as SAT. The paper gives medians for all five common sizes and observed min–max ranges for the large-board run; these ranges are descriptive, not confidence intervals. Local review notes, smoke-test outputs, and the verification script remain in the ignored `audit/` directory and are not part of the published dataset.

## Regenerate figures and manuscript

```powershell
python nqueens_sat/visualize.py
```

The six PDF/PNG figures in `nqueens_sat/results/figures/` and `report/figures/` retain the established GitHub layout while reflecting the corrected historical-data interpretation. The script writes both figure sets and a `figures_manifest.json` with the source CSV and output SHA-256 hashes. The best-SAT versus exact-method bar chart now includes recorded cases through N=200; at N=150 and N=200, Binary is the only SAT encoding measured. The cactus chart plots sorted per-case times rather than cumulative sums. Blank heatmap cells are unmeasured, and grey cells marked `L` denote archived CPLEX license failures. No bar-top values or arrows are added.

These six figures visualize the historical CSV only. The separate clean-source large-board results appear in a dedicated table in the manuscript so that the figure data and their provenance remain unambiguous.

Compile [`report/main.tex`](report/main.tex) with the bundled CAS files, [`report/references.bib`](report/references.bib), `report/thumbnails/`, and the generated `report/figures/` in place. A TeX distribution with BibTeX and the Elsevier CAS dependencies is required. The submitted PDF and source must be built together after edits; compiler-specific CAS box warnings should be checked against the rendered page.

## Layout

- `nqueens_sat/encoders/`: five AMO encoders and the shared N-Queens CNF model.
- `nqueens_sat/baselines/`: ILP and CP models.
- `nqueens_sat/run_benchmark.py`: maintained process-isolated runner; `benchmark.py` is a compatibility entry point.
- `nqueens_sat/visualize.py`: figure regeneration and provenance checks in the published GitHub layout.
- `report/`: Elsevier manuscript, bibliography, CAS assets, and figures.
- `nqueens_sat/results/benchmarks/`: published run-level benchmark data and metadata.
- `audit/`: private local review evidence and diagnostics, ignored by Git.
