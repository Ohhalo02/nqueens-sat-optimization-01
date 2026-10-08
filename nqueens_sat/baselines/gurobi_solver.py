import time
from .common import failure_result
try:
    import gurobipy as gp
    from gurobipy import GRB
except ImportError:
    gp = None

class GurobiSolver:
    def __init__(self):
        self.name = 'ILP-Gurobi'
    def solve(self, n, time_limit=300):
        t0 = time.perf_counter()
        if gp is None:
            return failure_result(self.name, n, t0)
        env = None
        m = None
        try:
            env = gp.Env(empty=True)
            env.setParam("OutputFlag", 0)
            env.start()
            m = gp.Model("nqueens", env=env)
            m.setParam('TimeLimit', time_limit)
            m.setParam('Threads', 1)
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
            
            decode_start = time.perf_counter()
            solution = None
            if m.SolCount > 0:
                solution = [(i,j) for i in range(n) for j in range(n) if x[i,j].X > 0.5]
            if solution is not None:
                status = 'SAT'
            elif m.status == GRB.INFEASIBLE:
                status = 'UNSAT'
            elif m.status == GRB.TIME_LIMIT:
                status = 'TIMEOUT'
            else:
                status = 'UNKNOWN'
            decode_time = time.perf_counter() - decode_start
            return {
                'status': status,
                'native_status': int(m.status),
                'satisfiable': True if status == 'SAT' else False if status == 'UNSAT' else None,
                'solution': solution, 'num_vars': n*n, 'num_clauses': m.NumConstrs, 'num_aux_vars': 0,
                'encoding_time': encoding_time, 'solving_time': solving_time, 'decode_time': decode_time,
                'total_time': encoding_time + solving_time, 'wall_total': time.perf_counter() - t0,
                'encoder_name': self.name
            }
        except Exception as exc:
            return failure_result(self.name, n, t0, exc)
        finally:
            if m is not None:
                m.dispose()
            if env is not None:
                env.dispose()
