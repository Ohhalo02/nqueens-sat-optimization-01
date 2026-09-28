"""Focused benchmark - runs faster for practical results."""
import sys
import os
import time
import csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')

from encoders.binomial import BinomialEncoder
from encoders.binary import BinaryEncoder
from encoders.commander import CommanderEncoder
from encoders.sequential import SequentialEncoder
from encoders.product import ProductEncoder
from baselines.ilp_solver import ILPSolver
from baselines.cp_solver import CPSolver
from baselines.gurobi_solver import GurobiSolver
from baselines.cplex_mip_solver import CplexMIPSolver
from baselines.cplex_cp_solver import CplexCPSolver
from utils import validate_solution

TIMEOUT = 120  # seconds
RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
RESULTS_FILE = os.path.join(RESULTS_DIR, 'benchmark_results.csv')

def run_single(solver_class, n):
    """Run a single solver for a given N. Returns result dict or None on error."""
    try:
        solver = solver_class()
        start = time.perf_counter()
        result = solver.solve(n, TIMEOUT)
        elapsed = time.perf_counter() - start
        if elapsed > TIMEOUT:
            return None  # Exceeded timeout
        return result
    except Exception as e:
        print(f"    ERROR: {e}")
        return None

def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    # Define solvers and their max N thresholds (to avoid wasting time)
    solvers_config = [
        (BinomialEncoder,   [4, 8, 10, 15, 20, 25, 30, 40, 50, 75, 100]),
        (BinaryEncoder,     [4, 8, 10, 15, 20, 25, 30, 40, 50, 75, 100]),
        (CommanderEncoder,  [4, 8, 10, 15, 20, 25, 30, 40, 50, 75, 100]),
        (SequentialEncoder, [4, 8, 10, 15, 20, 25, 30, 40, 50, 75, 100]),
        (ProductEncoder,    [4, 8, 10, 15, 20, 25, 30, 40, 50]),
        (ILPSolver,         [4, 8, 10, 15, 20, 25, 30, 40, 50, 75, 100]),
        (CPSolver,          [4, 8, 10, 15, 20, 25, 30, 40, 50, 75, 100, 150, 200]),
        (GurobiSolver,      [4, 8, 10, 15, 20, 25, 30, 40, 50, 75, 100]),
        (CplexMIPSolver,    [4, 8, 10, 15, 20, 25, 30, 40, 50, 75, 100]),
        (CplexCPSolver,     [4, 8, 10, 15, 20, 25, 30, 40, 50, 75, 100, 150, 200]),
    ]
    
    # Write CSV header
    with open(RESULTS_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['encoder_name', 'n', 'num_vars', 'num_clauses', 'num_aux_vars',
                         'encoding_time', 'solving_time', 'total_time', 'satisfiable'])
    
    for solver_class, n_values in solvers_config:
        solver_name = solver_class.__name__ if hasattr(solver_class, '__name__') else solver_class().name
        print(f"\n=== {solver_name} ===")
        
        for n in n_values:
            print(f"  N={n}...", end=" ", flush=True)
            
            # Run 2 times, take average
            results = []
            for rep in range(2):
                r = run_single(solver_class, n)
                if r is None:
                    break
                results.append(r)
            
            if not results:
                # Record timeout
                with open(RESULTS_FILE, 'a', newline='') as f:
                    csv.writer(f).writerow([solver_name, n] + ['TIMEOUT'] * 7)
                print(f"TIMEOUT")
                break  # Skip larger N for this solver
            
            # Average times
            avg_enc = sum(r['encoding_time'] for r in results) / len(results)
            avg_solve = sum(r['solving_time'] for r in results) / len(results)
            avg_total = sum(r['total_time'] for r in results) / len(results)
            
            r0 = results[0]
            with open(RESULTS_FILE, 'a', newline='') as f:
                csv.writer(f).writerow([
                    r0['encoder_name'], n, r0['num_vars'], r0['num_clauses'],
                    r0.get('num_aux_vars', 0), f"{avg_enc:.6f}", f"{avg_solve:.6f}",
                    f"{avg_total:.6f}", r0['satisfiable']
                ])
            
            valid = validate_solution(r0['solution'], n) if r0['solution'] else False
            print(f"OK ({avg_total:.3f}s, {'VALID' if valid else 'INVALID'})")
    
    print(f"\n{'='*60}")
    print(f"Benchmark complete! Results saved to: {RESULTS_FILE}")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
