from .base import NQueensEncoder

class BinomialEncoder(NQueensEncoder):
    def _add_amo(self, variables):
        n = len(variables)
        for i in range(n):
            for j in range(i + 1, n):
                self.cnf.append([-variables[i], -variables[j]])
