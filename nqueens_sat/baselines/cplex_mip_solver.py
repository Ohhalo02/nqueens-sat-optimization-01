import time
try:
    from docplex.mp.model import Model
except ImportError:
    Model = None

class CplexMIPSolver:
    def __init__(self):
        self.name = 'ILP-CPLEX'
    def solve(self, n, time_limit=300):
        if Model is None: return {'satisfiable': False, 'solution': None, 'num_vars': n*n, 'num_clauses': 0, 'num_aux_vars': 0, 'encoding_time': 0, 'solving_time': float('inf'), 'total_time': float('inf'), 'encoder_name': self.name}
        t0 = time.perf_counter()
        try:
            m = Model(name='nqueens')
            m.set_time_limit(time_limit)
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
            
            solution = None
            if sol:
                solution = [(i,j) for i in range(n) for j in range(n) if sol.get_value(x[i,j]) > 0.5]
            return {
                'satisfiable': sol is not None, 'solution': solution, 'num_vars': n*n, 'num_clauses': m.number_of_constraints, 'num_aux_vars': 0,
                'encoding_time': encoding_time, 'solving_time': solving_time, 'total_time': encoding_time + solving_time, 'encoder_name': self.name
            }
        except Exception:
            return {'satisfiable': False, 'solution': None, 'num_vars': n*n, 'num_clauses': 0, 'num_aux_vars': 0, 'encoding_time': time.perf_counter()-t0, 'solving_time': float('inf'), 'total_time': float('inf'), 'encoder_name': self.name}
