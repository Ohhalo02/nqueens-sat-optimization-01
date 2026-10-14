# N-Queens SAT Encodings and Exact Solvers

Single-author course project comparing five AMO encodings (pairwise, binary, commander, sequential counter, product) with CBC, Gurobi, CPLEX MIP, OR-Tools CP-SAT, and CP Optimizer on empty boards. All SAT runs use Glucose4. The manuscript uses Elsevier's `cas-sc` class.

## Install

Use Python 3.14.4 to match the recorded environment. `requirements.txt` pins the seven direct open-source dependencies used in the experiments. Commercial backends require separately installed packages and suitable licenses.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

For IBM Standard, install the optional packages and connect them to the licensed native runtime:

```powershell
python -m pip install -r requirements-commercial.txt
python -m docplex.util.cli config --upgrade "C:\Program Files\IBM\ILOG\CPLEX_Studio222"
```

The licensed session used DOcplex 2.32.264, the `cplex` distribution 22.2.0.1, and Standard 22.2 native binaries. Adjust the Studio path to your installation. Metadata contain native-binary hashes and no credentials. Gurobi 13.0.3 needs a valid license; a WLS license also requires network access. Installing Python packages alone does not supply the commercial runtimes/licenses.

PuLP is pinned to 3.3.2 because this baseline uses its `PULP_CBC_CMD` API and bundled CBC. The wrapper uses temporary relative filenames so Windows paths containing spaces work. Run from a writable directory; `.cbc-*` scratch directories are removed on normal completion. A forcibly terminated worker can leave its scratch directory behind.

## Validate and benchmark

```powershell
python nqueens_sat/test_validation.py
python nqueens_sat/test_regressions.py -v
python nqueens_sat/test_validation.py --commercial
python nqueens_sat/run_benchmark.py --solvers BinaryEncoder ILP-Gurobi CP-SAT-ORTools --sizes 20 50 100 150 200 --repeats 3 --wall-limit 120
```

Public tests check exhaustive AMO input assignments through n=8, fresh-solver input unit propagation and AMO counts through n=64, exact board counts through N=12, and all projected placements through N=8 against independent permutation enumeration. CBC and CP-SAT are also checked on small boards. `--commercial` additionally tests Gurobi, CPLEX MIP, and CP Optimizer at N=1,2,3,4,8; missing packages or license limits are printed as skips, while unexpected errors fail. Without licenses, omit that command and the corresponding solver names. Regression tests cover CBC paths, CP stop causes, process deadlines, LF/CRLF artifact checks, and isolated figure output.

Each invocation creates a unique directory with `raw.csv`, `summary.csv`, `metadata.json`, and `runs.jsonl`. JSONL retains per-run status and placement for independent revalidation. A full-process deadline covers worker startup, solving, validation, and shutdown; timeout terminates the process tree. Medians require every requested repetition to finish with the same SAT/UNSAT status. `--output PATH` selects a new directory; existing datasets are never overwritten.

Use the runner to enforce SAT time limits: calling an encoder's `solve()` directly does not interrupt Glucose. Exact-solver APIs also receive a native time limit. Results preserve CP Optimizer stop causes and safe diagnostic codes/hints for errors. The process-tree termination implementation targets Windows, the experiment platform.

| Timing field | Boundary |
|---|---|
| `setup_time` | Explicit Gurobi environment/license startup; zero for backends without a separately timed setup step |
| `encoding_time` | Build CNF or exact model, after explicit setup |
| `solving_time` | Solver invocation, including loading or initialization performed inside that call |
| `total_time` | `encoding_time + solving_time`; excludes explicit setup and placement extraction |
| `wall_total` | Worker clock, including setup and extraction before returning the result |
| `process_wall_time` | Parent clock, including startup, validation, and shutdown |

Each metric's median is computed independently; adding component medians need not equal the median of per-run sums. SAT invocation includes Glucose initialization, loading, solving, model retrieval, and disposal. Native APIs have different overheads, so the primary metric is not an equivalent end-to-end latency measure.

Gurobi and CPLEX MIP use N² Boolean variables, 6N−6 constraints for N≥2, and a zero objective. Singleton diagonal inequalities are omitted. CBC retains its historical objective of maximizing queen count, fixed at N by the row equations, with the same feasible constraints. CP models use N column variables and three `AllDifferent` constraints.

## Data and provenance

The [archive](nqueens_sat/results/benchmark_results.csv) is immutable: 116 aggregate rows over 13 sizes, unequal coverage, and no preserved repetitions or complete collection protocol. An absent row is not a timeout; archived CPLEX license failures are not UNSAT.

Directories under [`results/benchmarks/`](nqueens_sat/results/benchmarks/) remain separate:

| Directory | Runs and role |
|---|---|
| `new_benchmark` | Earlier 45-run protocol check; modified source, excluded from the principal comparison |
| `common_small_benchmark` | 72 runs: eight methods × N=20,50,100 × three repeats |
| `large_n_benchmark` | 48 runs: eight methods × N=150,200 × three repeats; same source as the smaller session |
| `cplex_standard_benchmark` | 78 successful runs: two licensed IBM methods × 13 sizes × three repeats |
| `product75_benchmark` | Three successful Product N=75 runs; median 31.846 s |
| `gurobi_corrected_benchmark` | 15 successful runs after timing/model corrections; all placements retained |

The principal [`comparison.csv`](nqueens_sat/results/benchmarks/comparison.csv) selects **one session per method-size cell**, replacing earlier Gurobi common-size rows with corrected measurements. It covers ten methods at N=20,50,100,150,200: 150 repetitions, 141 SAT and nine deadlines. CBC N=20 and 200 and Sequential N=200 have no completion-time median. At N=200, corrected Gurobi has 40,000 variables, 1,194 constraints, a total-time median of 0.474 s, and a separate setup median of 0.006 s.

[`comparison_manifest.json`](nqueens_sat/results/benchmarks/comparison_manifest.json) records session fingerprints and file hashes. Current text-artifact hashes use `sha256-utf8-lf-v1`: decode UTF-8, normalize CRLF/CR to LF, then hash UTF-8 bytes. This tolerates Git newline conversion without ignoring data changes. Original collection-time source fingerprints in session metadata retain their original byte-based meaning; they are not claims that the current source is identical. [`coverage.csv`](nqueens_sat/results/benchmarks/coverage.csv) indexes all 130 cells without pooling repetitions. Earlier sessions did not retain placements; CSVs cannot support retrospective witness revalidation. Older Gurobi totals include environment startup and remain historical measurements, not reinterpreted with the corrected boundary.

[`runtime_spread.csv`](nqueens_sat/results/benchmarks/runtime_spread.csv) reports min/median/max construction-plus-invocation and full-process times for every common-size cell. The repeated SAT search counters are identical within each of the 24 completed SAT cells; timing repetitions are not independent instances. New integration tests and fixes do not replace historical measurements. New benchmark runs go to `results/runs/`; the manuscript selection continues to use the named sessions above.

All later sessions use three repetitions, one worker, and a 120-second full-process deadline. The comparison is descriptive: separate sessions, engine-default search settings apart from workers/deadline, one machine, and five feasible sizes. Min–max ranges are not confidence intervals. Current hardware verification identifies Windows 11, AMD Ryzen 7 8845H, 16 logical processors, and 27.8 GiB usable physical memory; session metadata retain their recorded environment identifiers.

## Regenerate figures and manuscript

```powershell
python nqueens_sat/prepare_comparison.py
python nqueens_sat/prepare_comparison.py --check
python nqueens_sat/visualize.py
```

The preparation script verifies repetitions, medians, exact formula counts, retained witnesses, and hashes of the recorded session files. It generates the common CSV, runtime ranges, and four LaTeX tables. Timeout formula sizes may be derived from exact counts; no cutoff is substituted for a completion runtime. `--check` compares text independently of LF/CRLF line endings and checks the manifest without rewriting it.

Six PDF/PNG figures in `nqueens_sat/results/figures/` and `report/figures/` use `comparison.csv`. Both sets are byte-identical, with manifests linking the normalized source-CSV hash and binary output hashes. Best SAT selects a median retrospectively per size, not one fixed encoder. Grey heatmap cells marked `T` are deadlines. Cactus curves sort medians over the same five attempted sizes; they do not sum runtimes or count repetitions as independent instances.

The manuscript includes three main figures: solver invocation, SAT versus exact, and cactus. Alternate datasets require an explicit output directory and never implicitly write to `report/figures`:

```powershell
python nqueens_sat/visualize.py --csv nqueens_sat/results/benchmark_results.csv --output-dir nqueens_sat/results/figures/historical
```

Compile [`report/main.tex`](report/main.tex) with the CAS files, [`references.bib`](report/references.bib), `report/tables/`, and `report/figures/`. Rebuild source and PDF together after changes and check compiler warnings against rendered pages.

For a local TeX installation, run `latexmk -pdf main.tex` inside `report/` (or `tectonic main.tex` with Tectonic). Then, from the repository root:

```powershell
python nqueens_sat/package_report.py
python nqueens_sat/package_report.py --check
```

This creates `report_overleaf.zip` with the current PDF, LaTeX sources, figures, tables, and a SHA-256 manifest. Creation refuses a PDF older than its source/assets; this timestamp guard does not prove that a PDF matches the source, so compile before packaging. `--check` compares archive contents against the current report, independently of checkout timestamps. TeX source line endings are normalized to LF; PDF/image hashes remain byte-exact. Select `main.tex` as the main document when importing the ZIP into Overleaf.

## Layout

- `nqueens_sat/encoders/` and `baselines/`: five AMO encoders and exact models.
- `run_benchmark.py`: process-isolated runner; `benchmark.py` delegates to it.
- `test_validation.py`: public correctness and propagation checks.
- `prepare_comparison.py`: reproducible data selection and table generation.
- `visualize.py`: figures in the established style.
- `report/`: manuscript, bibliography, CAS assets, tables, and figures.
