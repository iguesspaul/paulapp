import numpy as np
from scipy.optimize import minimize, minimize_scalar
from scipy.stats import poisson


def solve_lambda_from_odds(over_odds, under_odds):
    try:
        prob_o, prob_u = 1.0 / float(over_odds), 1.0 / float(under_odds)
        fair_prob_under = prob_u / (prob_o + prob_u)
        res = minimize_scalar(
            lambda lam: abs(poisson.cdf(2, lam) - fair_prob_under),
            bounds=(0.5, 8.0),
            method="bounded",
        )
        return float(res.x)
    except Exception:
        return None


def get_consensus_lambda(input_data):
    lambdas = {}
    for entry in input_data if isinstance(input_data, list) else [input_data]:
        book = entry.get("book", "Unknown")
        odds = entry.get("odds", entry)

        # Primary: Over/Under 2.5 method
        if "Over2.5" in odds and "Under2.5" in odds:
            val = solve_lambda_from_odds(odds["Over2.5"], odds["Under2.5"])
            if val:
                lambdas[book] = val
        # Fallback: 1x2-only — estimate lambda from draw probability
        # Higher draw prob implies lower scoring match
        elif all(k in odds for k in ["1", "X", "2"]):
            try:
                p1, px, p2 = 1.0 / float(odds["1"]), 1.0 / float(odds["X"]), 1.0 / float(odds["2"])
                sum_1x2 = p1 + px + p2
                Pd = px / sum_1x2
                # Rough estimate: draw probability ~2 * lambda * exp(-lambda) * Bessel approx
                # Simpler: fit lambda to Pd via lookup
                # For a match, draw prob peaks around lambda=2 at ~0.27
                # Use a simple heuristic scaled around the typical draw prob range
                lambda_est = max(0.8, min(4.0, 1.5 / Pd)) if Pd > 0 else 2.65
                lambdas[book] = lambda_est
                print(f"[LAMBDA] {book} 1x2-only estimate: Pd={Pd:.3f} -> lambda={lambda_est:.2f}")
            except Exception:
                pass

    # --- THE ANCHOR LOGIC ---
    # We trust Pinnacle (or 'Pinnacle Direct') above all else
    anchor = lambdas.get("Pinnacle Direct") or lambdas.get("Pinnacle")

    if not anchor:
        return sum(lambdas.values()) / len(lambdas) if lambdas else 2.65

    # Filter out any book that disagrees with Pinnacle by more than 15%
    valid_lambdas = [anchor]
    for book, val in lambdas.items():
        if "Pinnacle" in book:
            continue
        # If the book is within 15% of Pinnacle, we include it in the average
        if abs(val - anchor) / anchor < 0.15:
            valid_lambdas.append(val)
        else:
            print(f"[DATA TRASH] Discarding {book} (Lambda {val:.2f}) - Outlier detected.")

    return sum(valid_lambdas) / len(valid_lambdas)


def solve_implied_lambdas(Ph, Pd, Pu, rho=-0.10):
    """
    Fits home_lambda and away_lambda using a local optimization loop.

    If Pu is None, fits using only 1x2 probabilities (3 constraints for 2 params).
    If Pu is provided, uses all 4 constraints including O/U 2.5.

    Note: This creates temporary 7x7 Dixon-Coles Poisson grids inside the loss function
    to project match outcomes (Home, Draw, Away, Under 2.5) for candidate lambdas,
    comparing them against de-vigged sharp market probabilities to minimize error.
    """
    Pa = 1.0 - Ph - Pd

    def loss_full(params):
        """Full loss with O/U constraint."""
        L_h, L_a = params

        # Build 7x7 grid
        matrix = np.zeros((7, 7))
        for h in range(7):
            for a in range(7):
                prob = poisson.pmf(h, L_h) * poisson.pmf(a, L_a)

                # Dixon-Coles Tau Adjustment
                tau = 1.0
                if h == 0 and a == 0:
                    tau = 1.0 - rho * L_h * L_a
                elif h == 1 and a == 0:
                    tau = 1.0 + rho * L_a
                elif h == 0 and a == 1:
                    tau = 1.0 + rho * L_h
                elif h == 1 and a == 1:
                    tau = 1.0 - rho

                tau = max(0.0, tau)
                matrix[h][a] = prob * tau

        # Normalize
        total_prob = np.sum(matrix)
        if total_prob > 0:
            matrix /= total_prob

        g_h = 0.0
        g_d = 0.0
        g_a = 0.0
        g_u = 0.0
        for h in range(7):
            for a in range(7):
                if h > a:
                    g_h += matrix[h][a]
                elif a > h:
                    g_a += matrix[h][a]
                else:
                    g_d += matrix[h][a]

                if (h + a) < 2.5:
                    g_u += matrix[h][a]

        if Pu is not None:
            return (g_h - Ph) ** 2 + (g_d - Pd) ** 2 + (g_a - Pa) ** 2 + (g_u - Pu) ** 2
        else:
            return (g_h - Ph) ** 2 + (g_d - Pd) ** 2 + (g_a - Pa) ** 2

    def loss_1x2_only(params):
        """Loss with only 1x2 constraints (no O/U)."""
        L_h, L_a = params
        matrix = np.zeros((7, 7))
        for h in range(7):
            for a in range(7):
                prob = poisson.pmf(h, L_h) * poisson.pmf(a, L_a)
                tau = 1.0
                if h == 0 and a == 0:
                    tau = 1.0 - rho * L_h * L_a
                elif h == 1 and a == 0:
                    tau = 1.0 + rho * L_a
                elif h == 0 and a == 1:
                    tau = 1.0 + rho * L_h
                elif h == 1 and a == 1:
                    tau = 1.0 - rho
                tau = max(0.0, tau)
                matrix[h][a] = prob * tau
        total_prob = np.sum(matrix)
        if total_prob > 0:
            matrix /= total_prob
        g_h, g_d, g_a = 0.0, 0.0, 0.0
        for h in range(7):
            for a in range(7):
                if h > a:
                    g_h += matrix[h][a]
                elif a > h:
                    g_a += matrix[h][a]
                else:
                    g_d += matrix[h][a]
        return (g_h - Ph) ** 2 + (g_d - Pd) ** 2 + (g_a - Pa) ** 2

    loss_fn = loss_full if Pu is not None else loss_1x2_only
    res = minimize(loss_fn, x0=[1.3, 1.3], bounds=[(0.1, 10.0), (0.1, 10.0)], method="L-BFGS-B")
    if res.success:
        return float(res.x[0]), float(res.x[1])
    return 1.3, 1.3


def solve_implied_lambdas_from_consensus(input_data):
    entries = input_data if isinstance(input_data, list) else [input_data]

    # 1. Try to find Pinnacle first (must have at least 1x2 odds)
    pinnacle_entry = None
    for entry in entries:
        book = entry.get("book", "")
        if "Pinnacle" in book:
            odds = entry.get("odds", {})
            # Need at minimum '1', 'X', '2'
            if all(k in odds for k in ["1", "X", "2"]):
                pinnacle_entry = entry
                break

    # 2. Extract odds from best available entry
    target_entry = pinnacle_entry
    if not target_entry:
        for entry in entries:
            odds = entry.get("odds", {})
            if all(k in odds for k in ["1", "X", "2"]):
                target_entry = entry
                break

    if not target_entry:
        return None, None

    odds = target_entry.get("odds", {})
    try:
        o1, ox, o2 = float(odds["1"]), float(odds["X"]), float(odds["2"])

        p1, px, p2 = 1.0 / o1, 1.0 / ox, 1.0 / o2
        sum_1x2 = p1 + px + p2
        Ph = p1 / sum_1x2
        Pd = px / sum_1x2

        has_ou = all(k in odds for k in ["Over2.5", "Under2.5"])

        if has_ou:
            o_over, o_under = float(odds["Over2.5"]), float(odds["Under2.5"])
            po, pu = 1.0 / o_over, 1.0 / o_under
            sum_ou = po + pu
            Pu = pu / sum_ou
            L_h, L_a = solve_implied_lambdas(Ph, Pd, Pu)
            print(
                f"[SOLVER] Implied Lambdas via {target_entry.get('book', 'Unknown')}: Home={L_h:.4f}, Away={L_a:.4f} (fitted to Ph={Ph:.2%}, Pd={Pd:.2%}, Pu={Pu:.2%})"
            )
        else:
            L_h, L_a = solve_implied_lambdas(Ph, Pd, None)
            print(
                f"[SOLVER] Implied Lambdas via {target_entry.get('book', 'Unknown')} (1x2-only): Home={L_h:.4f}, Away={L_a:.4f} (fitted to Ph={Ph:.2%}, Pd={Pd:.2%})"
            )

        return L_h, L_a
    except Exception as e:
        print(f"[SOLVER] Failed to solve: {e}")
        return None, None


class SharpConsensus:
    def __init__(self):
        pass

    def calculate_consensus_lambda(self, sharp_results_list):
        return get_consensus_lambda(sharp_results_list)

    def solve_implied_lambdas(self, sharp_results_list):
        return solve_implied_lambdas_from_consensus(sharp_results_list)
