import time
from ortools.sat.python import cp_model

class CPSolver:
    def __init__(self):
        self.name = 'CP-SAT-ORTools'
    
    def solve(self, n, time_limit=300):
        t_start = time.perf_counter()
        
        model = cp_model.CpModel()
        
        # Variables: queens[i] = column of queen in row i
        queens = [model.NewIntVar(0, n - 1, f'q_{i}') for i in range(n)]
        
        # All columns different
        model.AddAllDifferent(queens)
        
        # All main diagonals different: queens[i] + i
        model.AddAllDifferent([queens[i] + i for i in range(n)])
        
        # All anti-diagonals different: queens[i] - i  
        model.AddAllDifferent([queens[i] - i for i in range(n)])
        
        encoding_time = time.perf_counter() - t_start
        
        t_solve = time.perf_counter()
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit
        status = solver.Solve(model)
        solving_time = time.perf_counter() - t_solve
        
        solution = None
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            solution = [(i, solver.Value(queens[i])) for i in range(n)]
        
        return {
            'satisfiable': status in (cp_model.OPTIMAL, cp_model.FEASIBLE),
            'solution': solution,
            'num_vars': n,  # N integer variables
            'num_clauses': 3,  # 3 AllDifferent constraints
            'num_aux_vars': 0,
            'encoding_time': encoding_time,
            'solving_time': solving_time,
            'total_time': encoding_time + solving_time,
            'encoder_name': self.name
        }
