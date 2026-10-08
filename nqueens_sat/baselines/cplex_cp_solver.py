import time
from .common import failure_result
try:
    from docplex.cp.model import CpoModel
except ImportError:
    CpoModel = None

class CplexCPSolver:
    def __init__(self):
        self.name = 'CP-CPLEX'
    def solve(self, n, time_limit=300):
        t0 = time.perf_counter()
        if CpoModel is None:
            return failure_result(self.name, n, t0, integer_variables=True)
        try:
            m = CpoModel()
            queens = m.integer_var_list(n, 0, n - 1, "Q")
            m.add(m.all_diff(queens))
            m.add(m.all_diff(queens[i] + i for i in range(n)))
            m.add(m.all_diff(queens[i] - i for i in range(n)))
            encoding_time = time.perf_counter() - t0
            t_solve = time.perf_counter()
            sol = m.solve(TimeLimit=time_limit, Workers=1, LogVerbosity='Quiet')
            solving_time = time.perf_counter() - t_solve
            
            decode_start = time.perf_counter()
            solution = None
            if sol is not None and sol.is_solution():
                solution = [(i, sol[queens[i]]) for i in range(n)]
            solve_status = str(sol.get_solve_status()).lower() if sol is not None else 'unknown'
            status = 'SAT' if solution is not None else 'UNSAT' if solve_status == 'infeasible' else 'TIMEOUT' if 'time limit' in solve_status else 'UNKNOWN'
            decode_time = time.perf_counter() - decode_start
            return {
                'status': status, 'native_status': solve_status,
                'satisfiable': True if status == 'SAT' else False if status == 'UNSAT' else None,
                'solution': solution, 'num_vars': n, 'num_clauses': 3, 'num_aux_vars': 0,
                'encoding_time': encoding_time, 'solving_time': solving_time, 'decode_time': decode_time,
                'total_time': encoding_time + solving_time, 'wall_total': time.perf_counter() - t0, 'encoder_name': self.name
            }
        except Exception as exc:
            return failure_result(self.name, n, t0, exc, integer_variables=True)
