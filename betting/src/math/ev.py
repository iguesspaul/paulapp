def calculate_ev(fair_prob, odds):
    """
    Calculates the Expected Value (EV) of a bet.
    EV = (Probability of Winning * Decimal Odds) - 1.0
    """
    return (fair_prob * odds) - 1.0

def calculate_fair_odds(fair_prob):
    """
    Calculates the true fair decimal odds based on the true probability.
    """
    if fair_prob <= 0:
        return 0.0
    return 1.0 / fair_prob
