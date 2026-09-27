import time
try:
    from docplex.cp.model import CpoModel
except ImportError:
    CpoModel = None

class CplexCPSolver:
    def __init__(self):
        self.name = 'CP-CPLEX'
    def solve(self, n, time_limit=300):
        if CpoModel is None: return {'satisfiable': False, 'solution': None, 'num_vars': n, 'num_clauses': 0, 'num_aux_vars': 0, 'encoding_time': 0, 'solving_time': float('inf'), 'total_time': float('inf'), 'encoder_name': self.name}
        t0 = time.perf_counter()
        try:
            m = CpoModel()
            queens = m.integer_var_list(n, 0, n - 1, "Q")
            m.add(m.all_diff(queens))
            m.add(m.all_diff(queens[i] + i for i in range(n)))
            m.add(m.all_diff(queens[i] - i for i in range(n)))
            encoding_time = time.perf_counter() - t0
            t_solve = time.perf_counter()
            sol = m.solve(TimeLimit=time_limit, LogVerbosity='Quiet')
            solving_time = time.perf_counter() - t_solve
            
            solution = None
            if sol and sol.is_solution():
                solution = [(i, sol[queens[i]]) for i in range(n)]
            return {
                'satisfiable': sol is not None and sol.is_solution(), 'solution': solution, 'num_vars': n, 'num_clauses': 3, 'num_aux_vars': 0,
                'encoding_time': encoding_time, 'solving_time': solving_time, 'total_time': encoding_time + solving_time, 'encoder_name': self.name
            }
        except Exception:
            return {'satisfiable': False, 'solution': None, 'num_vars': n, 'num_clauses': 0, 'num_aux_vars': 0, 'encoding_time': time.perf_counter()-t0, 'solving_time': float('inf'), 'total_time': float('inf'), 'encoder_name': self.name}
