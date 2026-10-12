"""Public checks of projected AMO semantics, input UP, counts, and placements."""
import itertools
import math
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
from pysat.solvers import Glucose4

SAT = (BinomialEncoder, BinaryEncoder, CommanderEncoder,
       SequentialEncoder, ProductEncoder)
BASELINES = (ILPSolver, CPSolver)


def amo_counts(solver_class, n):
    """Independent counts from the manuscript, including implementation cutoffs."""
    if n <= 1:
        return 0, 0
    if solver_class is BinomialEncoder or (solver_class is ProductEncoder and n < 6):
        return 0, math.comb(n, 2)
    if solver_class is BinaryEncoder:
        bits = (n - 1).bit_length()
        return bits, n * bits
    if solver_class is SequentialEncoder:
        return n - 1, 3 * n - 4
    if solver_class is ProductEncoder:
        p = math.isqrt(n - 1) + 1
        q = (n + p - 1) // p
        return p + q, 2 * n + math.comb(p, 2) + math.comb(q, 2) + p * q - n
    if n <= 3:
        return 0, math.comb(n, 2)
    groups = [min(3, n - start) for start in range(0, n, 3)]
    a, c = amo_counts(solver_class, len(groups))
    return len(groups) + a, sum(math.comb(g, 2) for g in groups) + n + len(groups) + c


def check_amo():
    for solver_class in SAT:
        for n in range(65):
            encoder = solver_class()
            encoder._next_var = n
            inputs = list(range(1, n + 1))
            encoder._add_amo(inputs)
            assert (encoder.num_aux_vars, len(encoder.cnf.clauses)) == amo_counts(solver_class, n)
            with Glucose4(bootstrap_with=encoder.cnf) as solver:
                if n <= 8:
                    for bits in itertools.product((False, True), repeat=n):
                        assumptions = [i if b else -i for i, b in zip(inputs, bits)]
                        assert solver.solve(assumptions=assumptions) == (sum(bits) <= 1), (solver_class, n, bits)
            # Fresh solver: no learned clauses from semantic checks may help UP.
            with Glucose4(bootstrap_with=encoder.cnf) as solver:
                for selected in inputs:
                    ok, propagated = solver.propagate(assumptions=[selected])
                    assert ok and {-i for i in inputs if i != selected} <= set(propagated), (solver_class, n, selected)
                    for other in inputs:
                        if other != selected:
                            assert not solver.propagate(assumptions=[selected, other])[0]
        print(f'{solver_class.__name__}: AMO semantics, counts, and input UP passed')


def reference_placements(n):
    """Independent permutation enumeration; does not use a SAT encoding."""
    return {cols for cols in itertools.permutations(range(n))
            if len({r - c for r, c in enumerate(cols)}) == n
            and len({r + c for r, c in enumerate(cols)}) == n}


def check_boards():
    known_counts = (1, 0, 0, 2, 10, 4, 40, 92)
    references = {n: reference_placements(n) for n in range(1, 9)}
    assert tuple(len(references[n]) for n in range(1, 9)) == known_counts
    for solver_class in SAT:
        for n in range(1, 13):
            encoder = solver_class()
            cnf = encoder.encode(n)
            if n == 1:
                expected_a, expected_c = 0, 2
            else:
                a, c = amo_counts(solver_class, n)
                expected_a = (2 * n + 2) * a + 4 * sum(amo_counts(solver_class, k)[0] for k in range(2, n))
                expected_c = 2 * n + (2 * n + 2) * c + 4 * sum(amo_counts(solver_class, k)[1] for k in range(2, n))
            assert (cnf.nv, len(cnf.clauses)) == (n * n + expected_a, expected_c)
            if n > 8:
                continue
            found = set()
            with Glucose4(bootstrap_with=cnf) as solver:
                while solver.solve():
                    positives = sorted(lit for lit in solver.get_model() if 0 < lit <= n * n)
                    placement = [((lit - 1) // n, (lit - 1) % n) for lit in positives]
                    assert validate_solution(placement, n)
                    found.add(tuple(c for _, c in placement))
                    # Block the board projection, not one auxiliary assignment.
                    solver.add_clause([-lit for lit in positives])
            assert found == references[n], (solver_class, n)
        print(f'{solver_class.__name__}: board counts and all placements through N=8 passed')


def main():
    check_amo()
    check_boards()
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
