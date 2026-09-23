import time
from abc import ABC, abstractmethod
from pysat.formula import CNF
from pysat.solvers import Glucose4

class NQueensEncoder(ABC):
    def __init__(self):
        self.cnf = CNF()
        self.n = 0
        self.num_aux_vars = 0
        self.encoding_time = 0.0
        self.solving_time = 0.0
        self._next_var = 0
    
    def var(self, i, j):
        """Map board position (i,j) to SAT variable. 0-indexed i,j."""
        return i * self.n + j + 1
    
    def new_var(self):
        """Allocate a new auxiliary variable."""
        self._next_var += 1
        self.num_aux_vars += 1
        return self._next_var
    
    def encode(self, n):
        """Build complete CNF formula for N-Queens."""
        self.cnf = CNF()
        self.n = n
        self.num_aux_vars = 0
        self._next_var = n * n  # aux vars start after board vars
        
        t0 = time.perf_counter()
        self._encode_constraints()
        self.encoding_time = time.perf_counter() - t0
        return self.cnf
    
    def _add_alo(self, variables):
        """At-Least-One: at least one variable must be true."""
        self.cnf.append(list(variables))
    
    @abstractmethod
    def _add_amo(self, variables):
        """At-Most-One: at most one variable can be true. Each subclass implements differently."""
        pass
    
    def _add_exo(self, variables):
        """Exactly-One = ALO + AMO."""
        self._add_alo(variables)
        self._add_amo(variables)
    
    def _encode_constraints(self):
        """Default implementation: EXO on rows/cols, AMO on diagonals."""
        n = self.n
        # Row constraints: exactly one queen per row
        for i in range(n):
            row_vars = [self.var(i, j) for j in range(n)]
            self._add_exo(row_vars)
        
        # Column constraints: exactly one queen per column
        for j in range(n):
            col_vars = [self.var(i, j) for i in range(n)]
            self._add_exo(col_vars)
        
        # Main diagonal constraints (r - c = const): AMO only
        for d in range(-(n-1), n):
            diag_vars = []
            for i in range(n):
                j = i - d
                if 0 <= j < n:
                    diag_vars.append(self.var(i, j))
            if len(diag_vars) >= 2:
                self._add_amo(diag_vars)
        
        # Anti-diagonal constraints (r + c = const): AMO only
        for s in range(0, 2*n - 1):
            anti_vars = []
            for i in range(n):
                j = s - i
                if 0 <= j < n:
                    anti_vars.append(self.var(i, j))
            if len(anti_vars) >= 2:
                self._add_amo(anti_vars)
    
    def solve(self, n, time_limit=300):
        """Encode and solve N-Queens. Returns dict with results."""
        self.encode(n)
        
        t0 = time.perf_counter()
        with Glucose4(bootstrap_with=self.cnf) as solver:
            sat = solver.solve()
            model = solver.get_model() if sat else None
        self.solving_time = time.perf_counter() - t0
        
        solution = None
        if model:
            solution = []
            for i in range(n):
                for j in range(n):
                    if self.var(i, j) in model:
                        solution.append((i, j))
        
        return {
            'satisfiable': sat,
            'solution': solution,
            'num_vars': self.cnf.nv,
            'num_clauses': len(self.cnf.clauses),
            'num_aux_vars': self.num_aux_vars,
            'encoding_time': self.encoding_time,
            'solving_time': self.solving_time,
            'total_time': self.encoding_time + self.solving_time,
            'encoder_name': self.__class__.__name__
        }
    
    @property
    def name(self):
        return self.__class__.__name__
