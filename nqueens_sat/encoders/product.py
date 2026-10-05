import math
from .base import NQueensEncoder

class ProductEncoder(NQueensEncoder):
    def _add_amo(self, variables):
        n = len(variables)
        if n < 6:
            for i in range(n):
                for j in range(i + 1, n):
                    self.cnf.append([-variables[i], -variables[j]])
            return
            
        p = math.ceil(math.sqrt(n))
        q = math.ceil(n / p)
        
        u = [self.new_var() for _ in range(p)]
        v = [self.new_var() for _ in range(q)]
        
        for k, x in enumerate(variables):
            r = k // q
            c = k % q
            self.cnf.append([-x, u[r]])
            self.cnf.append([-x, v[c]])
            
        # Phantom positions (if any)
        for r in range(p):
            for c in range(q):
                if r * q + c >= n:
                    self.cnf.append([-u[r], -v[c]])
                    
        # Pairwise AMO on u's
        for i in range(p):
            for j in range(i + 1, p):
                self.cnf.append([-u[i], -u[j]])
                
        # Pairwise AMO on v's
        for i in range(q):
            for j in range(i + 1, q):
                self.cnf.append([-v[i], -v[j]])
