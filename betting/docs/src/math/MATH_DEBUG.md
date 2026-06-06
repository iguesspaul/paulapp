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
- **`solve_implied_lambdas(Ph, Pd, Pu)`**: Solves for home/away lambdas using the 7x7 Dixon-Coles grid via `scipy.optimize.minimize`. If `Pu` is provided, uses all 4 constraints (H, D, A, U2.5). If `Pu=None`, uses 3 constraints (H, D, A — 1x2-only mode) which is still sufficient for 2 parameters.
- **`solve_implied_lambdas_from_consensus(input_data)`**: Main solver entry point. Extracts odds from Pinnacle (preferred) or the best available sharp source. De-vigs 1x2 and O/U 2.5 (when available) and calls `solve_implied_lambdas`. Falls back to 1x2-only mode when O/U isn't available.
- **`get_consensus_lambda(input_data)`**: Fallback consensus solver. Primary: reverse-engineers lambda from O/U 2.5 odds. Fallback: estimates lambda from draw probability using `lambda = clamp(1.5/Pd, 0.8, 4.0)` when only 1x2 odds are available.
- **`solve_lambda_from_odds(over_odds, under_odds)`**: Reverse-engineers a Poisson Lambda from a de-vigged Under 2.5 probability.
- **1x2-Only Logging**: Prints `[SOLVER] Implied Lambdas via ... (1x2-only):` when using the 3-constraint fallback, and `[LAMBDA] book 1x2-only estimate:` for the heuristic lambda estimate.

## Grid Generation Architecture

Both `sharp_consensus.py` and `probability_grid.py` construct 7x7 Dixon-Coles Poisson probability grids, but they serve different purposes in the pipeline:

1. **Optimization Fitting (`sharp_consensus.py`)**:
   - **Purpose**: Solves for unknown parameters (`home_lambda` and `away_lambda`).
   - **How it works**: The Scipy solver starts with initial guesses for the lambdas, builds a temporary 7x7 grid inside the optimizer's loss function loop, and sums the probabilities of Home win, Draw, Away win, and Under 2.5 goals. It compares these sums to the de-vigged sharp market odds. The solver repeats this grid construction process iteratively until the loss is minimized, determining the most accurate implied lambdas representing the sharp bookmaker consensus.

2. **Market Pricing (`probability_grid.py`)**:
   - **Purpose**: Translates the solved lambdas into final fair probabilities for all betting markets.
   - **How it works**: Once the sharp consensus lambdas are determined, they are passed to the `ProbabilityGrid` constructor to build three static 7x7 matrices (Full Match, 1st Half, 2nd Half). The `MarketResolver` queries these static matrices to compute the final fair prices of complex casino markets (e.g. correct score, double chance & BTTS), which are compared against casino prices to find EV.
