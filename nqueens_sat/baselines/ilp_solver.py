from pulp import *
import time

class ILPSolver:
    def __init__(self):
        self.name = 'ILP-PuLP-CBC'
    
    def solve(self, n, time_limit=300):
        t_start = time.perf_counter()
        
        # Create problem
        prob = LpProblem('NQueens', LpMaximize)
        
        # Binary variables x[i][j]
        x = [[LpVariable(f'x_{i}_{j}', cat='Binary') for j in range(n)] for i in range(n)]
        
        # Objective: maximize total queens (should be N for feasible)
        prob += lpSum(x[i][j] for i in range(n) for j in range(n))
        
        # Row constraints: exactly one queen per row
        for i in range(n):
            prob += lpSum(x[i][j] for j in range(n)) == 1
        
        # Column constraints: exactly one queen per column  
        for j in range(n):
            prob += lpSum(x[i][j] for i in range(n)) == 1
        
        # Main diagonal constraints: at most one queen
        for d in range(-(n-1), n):
            diag_vars = [x[i][i-d] for i in range(n) if 0 <= i-d < n]
            if len(diag_vars) >= 2:
                prob += lpSum(diag_vars) <= 1
        
        # Anti-diagonal constraints: at most one queen
        for s in range(0, 2*n - 1):
            anti_vars = [x[i][s-i] for i in range(n) if 0 <= s-i < n]
            if len(anti_vars) >= 2:
                prob += lpSum(anti_vars) <= 1
        
        encoding_time = time.perf_counter() - t_start
        
        t_solve = time.perf_counter()
        # Solve with CBC, suppress output
        prob.solve(PULP_CBC_CMD(msg=0, timeLimit=time_limit))
        solving_time = time.perf_counter() - t_solve
        
        solution = None
        if prob.status == 1:  # Optimal
            solution = []
            for i in range(n):
                for j in range(n):
                    if value(x[i][j]) > 0.5:
                        solution.append((i, j))
        
        # Count variables and constraints
        num_vars = n * n
        num_constraints = prob.numConstraints()
        
        return {
            'satisfiable': prob.status == 1,
            'solution': solution,
            'num_vars': num_vars,
            'num_clauses': num_constraints,  # for uniform naming
            'num_aux_vars': 0,
            'encoding_time': encoding_time,
            'solving_time': solving_time,
            'total_time': encoding_time + solving_time,
            'encoder_name': self.name
        }
