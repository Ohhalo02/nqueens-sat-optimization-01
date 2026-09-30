# N-Queens SAT Solvers and Baselines

This project contains various SAT encoders and baseline exact solvers (ILP, CP) for the N-Queens problem.

## Installation

```bash
pip install -r requirements.txt
```

## Structure

- `encoders/`: Contains various SAT encoding methods (Binomial, Binary, Commander, Sequential, Product)
- `baselines/`: Contains exact solvers:
  - `ilp_solver.py`: ILP model using PuLP and CBC
  - `cp_solver.py`: Constraint Programming model using Google OR-Tools CP-SAT
- `benchmark.py`: Script to benchmark all methods across different N values
- `visualize.py`: Script to generate publication-quality figures

## Usage

To run the full benchmark:
```bash
python benchmark.py
```

To generate visualizations from results:
```bash
python visualize.py
```

## Results
(Results will be populated in `results/benchmark_results.csv` and figures in `results/figures/`)
