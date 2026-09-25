from .base import NQueensEncoder

class SequentialEncoder(NQueensEncoder):
    def _add_amo(self, variables):
        n = len(variables)
        if n <= 1:
            return
            
        s = [self.new_var() for _ in range(n - 1)]
        
        self.cnf.append([-variables[0], s[0]])
        
        for i in range(1, n - 1):
            self.cnf.append([-variables[i], s[i]])
            self.cnf.append([-s[i-1], s[i]])
            self.cnf.append([-variables[i], -s[i-1]])
            
        self.cnf.append([-variables[n-1], -s[n-2]])
