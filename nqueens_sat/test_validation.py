"""Quick validation test for all N-Queens SAT encoders and baseline solvers."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')

from encoders.binomial import BinomialEncoder
from encoders.binary import BinaryEncoder
from encoders.commander import CommanderEncoder
from encoders.sequential import SequentialEncoder
from encoders.product import ProductEncoder
from baselines.ilp_solver import ILPSolver
from baselines.cp_solver import CPSolver
from utils import validate_solution, print_board

def test_encoder(encoder_class, n_values=[4, 8]):
    """Test an encoder for given N values."""
    name = encoder_class.__name__ if hasattr(encoder_class, '__name__') else encoder_class().name
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"{'='*60}")
    
    for n in n_values:
        try:
            solver = encoder_class()
            result = solver.solve(n)
            valid = validate_solution(result['solution'], n) if result['solution'] else False
            
            status = "VALID" if valid else "INVALID"
            print(f"  N={n:3d} | {status:>7s} | "
                  f"Vars={result['num_vars']:6d} | "
                  f"Clauses={result['num_clauses']:8d} | "
                  f"Aux={result.get('num_aux_vars', 0):6d} | "
                  f"Enc={result['encoding_time']:.4f}s | "
                  f"Solve={result['solving_time']:.4f}s | "
                  f"Total={result['total_time']:.4f}s")
            
            if n == 4 and valid:
                print(f"  Solution: {result['solution']}")
                
        except Exception as e:
            print(f"  N={n:3d} | ERROR: {e}")

if __name__ == '__main__':
    # Test all SAT encoders
    sat_encoders = [BinomialEncoder, BinaryEncoder, CommanderEncoder, SequentialEncoder, ProductEncoder]
    for enc in sat_encoders:
        test_encoder(enc, n_values=[4, 8, 20, 50])
    
    # Test baseline solvers
    baseline_solvers = [ILPSolver, CPSolver]
    for solver in baseline_solvers:
        test_encoder(solver, n_values=[4, 8, 20, 50])
    
    print(f"\n{'='*60}")
    print("All tests completed!")
    print(f"{'='*60}")
