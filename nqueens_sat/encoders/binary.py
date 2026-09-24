import math
from .base import NQueensEncoder

class BinaryEncoder(NQueensEncoder):
    def _add_amo(self, variables):
        n = len(variables)
        if n <= 1:
            return
        m = math.ceil(math.log2(n))
        aux_vars = [self.new_var() for _ in range(m)]
        
        for k, x in enumerate(variables):
            for b in range(m):
                if (k >> b) & 1:
                    self.cnf.append([-x, aux_vars[b]])
                else:
                    self.cnf.append([-x, -aux_vars[b]])
