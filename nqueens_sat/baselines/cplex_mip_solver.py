import time
from .common import failure_result
try:
    from docplex.mp.model import Model
except ImportError:
    Model = None

class CplexMIPSolver:
    def __init__(self):
        self.name = 'ILP-CPLEX'
    def solve(self, n, time_limit=300):
        t0 = time.perf_counter()
        if Model is None:
            return failure_result(self.name, n, t0)
        m = None
        try:
            m = Model(name='nqueens')
            m.set_time_limit(time_limit)
            m.context.cplex_parameters.threads = 1
            x = {(i,j): m.binary_var(name=f'x_{i}_{j}') for i in range(n) for j in range(n)}
            for i in range(n): m.add_constraint(m.sum(x[i,j] for j in range(n)) == 1)
            for j in range(n): m.add_constraint(m.sum(x[i,j] for i in range(n)) == 1)
            for d in range(-(n-1), n):
                vars_diag = [x[i, i-d] for i in range(n) if 0 <= i-d < n]
                if len(vars_diag) > 1: m.add_constraint(m.sum(vars_diag) <= 1)
            for s in range(0, 2*n - 1):
                vars_anti = [x[i, s-i] for i in range(n) if 0 <= s-i < n]
                if len(vars_anti) > 1: m.add_constraint(m.sum(vars_anti) <= 1)
            encoding_time = time.perf_counter() - t0
            t_solve = time.perf_counter()
            sol = m.solve(log_output=False)
            solving_time = time.perf_counter() - t_solve
            
            decode_start = time.perf_counter()
            solution = None
            if sol:
                solution = [(i,j) for i in range(n) for j in range(n) if sol.get_value(x[i,j]) > 0.5]
            solve_status = str(m.solve_details.status).lower()
            status = 'SAT' if solution is not None else 'UNSAT' if 'infeasible' in solve_status else 'TIMEOUT' if 'time limit' in solve_status else 'UNKNOWN'
            decode_time = time.perf_counter() - decode_start
            return {
                'status': status, 'native_status': solve_status,
                'satisfiable': True if status == 'SAT' else False if status == 'UNSAT' else None,
                'solution': solution, 'num_vars': n*n, 'num_clauses': m.number_of_constraints, 'num_aux_vars': 0,
                'encoding_time': encoding_time, 'solving_time': solving_time, 'decode_time': decode_time,
                'total_time': encoding_time + solving_time, 'wall_total': time.perf_counter() - t0, 'encoder_name': self.name
            }
        except Exception as exc:
            return failure_result(self.name, n, t0, exc)
        finally:
            if m is not None:
                m.end()
