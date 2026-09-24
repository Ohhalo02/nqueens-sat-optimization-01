from .base import NQueensEncoder

class CommanderEncoder(NQueensEncoder):
    def _add_amo(self, variables):
        self._commander_amo(variables)
        
    def _commander_amo(self, variables):
        n = len(variables)
        if n <= 3:
            for i in range(n):
                for j in range(i + 1, n):
                    self.cnf.append([-variables[i], -variables[j]])
            return
            
        g = 3
        commanders = []
        for start_idx in range(0, n, g):
            group = variables[start_idx:min(start_idx + g, n)]
            
            # pairwise AMO within group
            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    self.cnf.append([-group[i], -group[j]])
            
            c_k = self.new_var()
            commanders.append(c_k)
            
            # if x in group is true, commander must be true
            for x in group:
                self.cnf.append([-x, c_k])
                
        # Recursively apply commander encoding on commanders
        self._commander_amo(commanders)
