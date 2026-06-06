import numpy as np
from scipy.stats import poisson

class ProbabilityGrid:
    """
    Constructs the final, canonical 7x7 Dixon-Coles Poisson probability grids 
    for Full Match, 1st Half, and 2nd Half using the solved/consensus lambdas.
    These grids are static and queried by MarketResolver to price casino betting markets.
    """
    def __init__(self, match_lambda=None, home_lambda=None, away_lambda=None, ht_lambda=None, rho=-0.10):
        self.rho = rho
        
        # Full Match
        if home_lambda is not None and away_lambda is not None:
            self.home_lambda = home_lambda
            self.away_lambda = away_lambda
            self.match_lambda = home_lambda + away_lambda
        else:
            if match_lambda is None:
                match_lambda = 2.65
            self.match_lambda = match_lambda
            self.home_lambda = match_lambda * 0.53
            self.away_lambda = match_lambda * 0.47
            
        self.grid = self._generate_matrix(self.home_lambda, self.away_lambda)
        
        # 1st Half Logic
        if ht_lambda is not None:
            self.h1_lambda = ht_lambda * 0.53
            self.a1_lambda = ht_lambda * 0.47
        else:
            self.h1_lambda = self.home_lambda * 0.45
            self.a1_lambda = self.away_lambda * 0.45
            print("\nWARNING: HEURISTIC SPLIT - No HT_LAMBDA provided. Falling back to 45% of MATCH_LAMBDA.\n")
                
        self.h1_grid = self._generate_matrix(self.h1_lambda, self.a1_lambda)
        
        # 2nd Half Logic (MATCH_LAMBDA - HT_LAMBDA)
        actual_ht_lambda = self.h1_lambda + self.a1_lambda
        h2_total = self.match_lambda - actual_ht_lambda
        
        self.h2_lambda = h2_total * 0.53
        self.a2_lambda = h2_total * 0.47
        self.h2_grid = self._generate_matrix(self.h2_lambda, self.a2_lambda)

    def _generate_matrix(self, h_lam, a_lam):
        matrix = np.zeros((7, 7))
        for h in range(7):
            for a in range(7):
                prob = poisson.pmf(h, h_lam) * poisson.pmf(a, a_lam)
                
                # Dixon-Coles Tau Adjustment
                tau = 1.0
                if h == 0 and a == 0:
                    tau = 1.0 - self.rho * h_lam * a_lam
                elif h == 1 and a == 0:
                    tau = 1.0 + self.rho * a_lam
                elif h == 0 and a == 1:
                    tau = 1.0 + self.rho * h_lam
                elif h == 1 and a == 1:
                    tau = 1.0 - self.rho
                
                # Ensure tau doesn't produce negative probabilities
                tau = max(0.0, tau)
                matrix[h][a] = prob * tau
                
        # Normalize the grid to ensure it sums perfectly to 1.0
        total_prob = np.sum(matrix)
        if total_prob > 0:
            matrix /= total_prob
            
        return matrix
