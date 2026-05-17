# Sentinel Quant Agent — `src/math/` (MATH_DEBUG) Documentation

## Files

### `bankroll_manager.py`
Staking logic based on the Kelly Criterion.
- **`calculate_kelly_stake(odds, fair_prob, bankroll, multiplier)`**: Calculates the optimal $ amount to bet on an edge.
  - *Inputs*: odds, fair probability, current bankroll, fractional Kelly multiplier.
  - *Outputs*: Float (stake amount).
  - *Error Risk*: Low. Purely mathematical.

### `probability_grid.py`
Generates 7x7 Poisson probability matrices for score distribution.
- **`ProbabilityGrid.__init__(match_lambda, home_lambda, away_lambda, ht_lambda)`**: Initializes the grid for Full Match, 1st Half, and 2nd Half. Supports direct initialization with Home and Away lambdas or standard match lambda splits.
- **`_generate_matrix(h_lam, a_lam)`**: Core Poisson PMF calculation for each score coordinate (0-0 to 6-6) incorporating the Dixon-Coles tau adjustment.
  - *Inputs*: Home lambda, Away lambda.
  - *Outputs*: 7x7 NumPy array.

### `sharp_consensus.py`
Calculates the "Fair Price" by resolving sharp market indicators.
- **`SharpConsensus.solve_implied_lambdas(sharp_results_list)`**: Implements the Top-Down Market Implied Constraint Solver. De-vigs Pinnacle's 1x2 and Under 2.5 odds to find exact $L_{home}$ and $L_{away}$ via `scipy.optimize.minimize` (L-BFGS-B) to perfectly reflect Pinnacle's score and margin distribution in the 7x7 grid.
- **`SharpConsensus.calculate_consensus_lambda(sharp_results_list)`**: Fallback consensus solver that reverse-engineers a match lambda from Over/Under 2.5 odds and averages across trusted sharp books.
- **`solve_lambda_from_odds(over_odds, under_odds)`**: Reverse-engineers a Poisson Lambda from a de-vigged Under 2.5 probability.
