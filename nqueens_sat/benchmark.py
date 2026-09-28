import sys
import os
import time
import csv
import pandas as pd
from concurrent.futures import ProcessPoolExecutor, TimeoutError
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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

N_VALUES = [4, 8, 10, 15, 20, 25, 30, 40, 50, 75, 100, 150, 200]
TIMEOUT = 300
NUM_REPEATS = 3
RESULTS_FILE = 'results/benchmark_results.csv'

def run_solver(solver_class, n, time_limit):
    solver = solver_class()
    return solver.solve(n, time_limit)

def main():
    os.makedirs('results', exist_ok=True)
    
    solvers = [
        BinomialEncoder,
        BinaryEncoder,
        CommanderEncoder,
        SequentialEncoder,
        ProductEncoder,
        ILPSolver,
        GurobiSolver,
        CplexMIPSolver,
        CplexCPSolver,
        CPSolver
    ]
    
    results = []
    
    # Initialize CSV file with headers
    with open(RESULTS_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['encoder_name', 'n', 'num_vars', 'num_clauses', 'num_aux_vars', 'encoding_time', 'solving_time', 'total_time', 'satisfiable'])
    
    for solver_class in solvers:
        dummy_solver = solver_class()
        solver_name = dummy_solver.name
        
        for n in N_VALUES:
            print(f"Running {solver_name} for N={n}...")
            
            run_results = []
            timeout_occurred = False
            
            for i in range(NUM_REPEATS):
                try:
                    with ProcessPoolExecutor(max_workers=1) as executor:
                        future = executor.submit(run_solver, solver_class, n, TIMEOUT)
                        res = future.result(timeout=TIMEOUT + 10) # extra padding for overhead
                        
                        run_results.append(res)
                except TimeoutError:
                    timeout_occurred = True
                    print(f"  Run {i+1} TIMEOUT")
                    break
                except Exception as e:
                    print(f"  Run {i+1} ERROR: {e}")
                    timeout_occurred = True
                    break
            
            if timeout_occurred or len(run_results) == 0:
                with open(RESULTS_FILE, mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([solver_name, n, 'TIMEOUT', 'TIMEOUT', 'TIMEOUT', 'TIMEOUT', 'TIMEOUT', 'TIMEOUT', 'TIMEOUT'])
                print(f"  {solver_name} N={n} reached TIMEOUT or ERROR")
                break # Stop running higher N for this solver
            else:
                avg_encoding = sum(r['encoding_time'] for r in run_results) / len(run_results)
                avg_solving = sum(r['solving_time'] for r in run_results) / len(run_results)
                avg_total = sum(r['total_time'] for r in run_results) / len(run_results)
                
                res = run_results[0] # assume vars/clauses same across runs
                
                with open(RESULTS_FILE, mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([
                        res['encoder_name'], n, res['num_vars'], res['num_clauses'], res.get('num_aux_vars', 0),
                        avg_encoding, avg_solving, avg_total, res['satisfiable']
                    ])
                print(f"  Completed {solver_name} N={n} in {avg_total:.2f}s")
    
    print("Benchmarking finished!")

if __name__ == '__main__':
    # Fix for ProcessPoolExecutor on Windows
    import multiprocessing
    multiprocessing.freeze_support()
    main()

