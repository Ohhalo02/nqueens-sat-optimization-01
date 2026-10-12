# N-Queens SAT solvers and exact baselines

Five AMO encodings use Glucose4. Exact baselines are CBC, Gurobi, CPLEX MIP, OR-Tools CP-SAT, and IBM CP Optimizer. See the [project README](../README.md) for installation, licenses, timing, and provenance. This revision is local and has not been pushed.

From this directory:

```powershell
python test_validation.py
python run_benchmark.py --solvers ILP-CPLEX CP-CPLEX --sizes 20 50 100 150 200 --repeats 3 --wall-limit 120
python prepare_comparison.py
python prepare_comparison.py --check
python visualize.py
```

The runner creates raw repetitions, medians, metadata, and JSONL witnesses in a unique run directory. Placements are validated before recording SAT. Old data and `results/benchmark_results.csv` remain unchanged. Earlier sessions did not preserve placements; only new runs provide witness files.

The principal [comparison](results/benchmarks/comparison.csv) selects one source session per cell for ten methods at five common sizes, including corrected Gurobi results. Earlier Gurobi records remain in their original directories. The [manifest](results/benchmarks/comparison_manifest.json) records provenance and hashes; the [coverage index](results/benchmarks/coverage.csv) covers all 130 method-size cells. Repetitions are not pooled across sessions.

`prepare_comparison.py` verifies medians, counts, and witnesses and generates manuscript tables. `visualize.py` writes six figures to both `results/figures/` and `../report/figures/`, preserving the established style and checking identical hashes. Three main figures appear in the shorter manuscript; the others remain available in the package.
