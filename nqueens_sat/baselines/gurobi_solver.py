import time
try:
    import gurobipy as gp
    from gurobipy import GRB
except ImportError:
    gp = None

class GurobiSolver:
    def __init__(self):
        self.name = 'ILP-Gurobi'
    def solve(self, n, time_limit=300):
        if gp is None: return {'satisfiable': False, 'solution': None, 'num_vars': n*n, 'num_clauses': 0, 'num_aux_vars': 0, 'encoding_time': 0, 'solving_time': float('inf'), 'total_time': float('inf'), 'encoder_name': self.name}
        t0 = time.perf_counter()
        try:
            env = gp.Env(empty=True)
            env.setParam("OutputFlag", 0)
            env.start()
            m = gp.Model("nqueens", env=env)
            m.setParam('TimeLimit', time_limit)
            x = m.addVars(n, n, vtype=GRB.BINARY, name="x")
            m.addConstrs((x.sum(i, '*') == 1 for i in range(n)))
            m.addConstrs((x.sum('*', j) == 1 for j in range(n)))
            for d in range(-(n-1), n):
                m.addConstr(gp.quicksum(x[i, i-d] for i in range(n) if 0 <= i-d < n) <= 1)
            for s in range(0, 2*n - 1):
                m.addConstr(gp.quicksum(x[i, s-i] for i in range(n) if 0 <= s-i < n) <= 1)
            
            encoding_time = time.perf_counter() - t0
            t_solve = time.perf_counter()
            m.optimize()
            solving_time = time.perf_counter() - t_solve
            
            solution = None
            if m.status == GRB.OPTIMAL:
                solution = [(i,j) for i in range(n) for j in range(n) if x[i,j].X > 0.5]
            return {
                'satisfiable': m.status == GRB.OPTIMAL,
                'solution': solution, 'num_vars': n*n, 'num_clauses': m.NumConstrs, 'num_aux_vars': 0,
                'encoding_time': encoding_time, 'solving_time': solving_time,
                'total_time': encoding_time + solving_time, 'encoder_name': self.name
            }
        except Exception:
            return {'satisfiable': False, 'solution': None, 'num_vars': n*n, 'num_clauses': 0, 'num_aux_vars': 0, 'encoding_time': time.perf_counter()-t0, 'solving_time': float('inf'), 'total_time': float('inf'), 'encoder_name': self.name}
