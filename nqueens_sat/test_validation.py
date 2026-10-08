"""Fast assertions for all five SAT encodings and the two open baselines."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from encoders.binomial import BinomialEncoder
from encoders.binary import BinaryEncoder
from encoders.commander import CommanderEncoder
from encoders.sequential import SequentialEncoder
from encoders.product import ProductEncoder
from baselines.ilp_solver import ILPSolver
from baselines.cp_solver import CPSolver
from utils import validate_solution

SAT = (BinomialEncoder, BinaryEncoder, CommanderEncoder,
       SequentialEncoder, ProductEncoder)
BASELINES = (ILPSolver, CPSolver)


def main():
    for solver_class in SAT + BASELINES:
        for n in (1, 2, 3, 4, 8):
            result = solver_class().solve(n)
            expected = n not in (2, 3)
            assert result['status'] == ('SAT' if expected else 'UNSAT'), (solver_class.__name__, n, result)
            assert result['satisfiable'] is expected, (solver_class.__name__, n, result)
            if expected:
                assert validate_solution(result['solution'], n), (solver_class.__name__, n, result)
            print(f'{solver_class.__name__} N={n}: {result["status"]}')
    print('All small-board validation assertions passed.')


if __name__ == '__main__':
    main()
