def calculate_kelly_stake(odds, fair_prob, bankroll, multiplier=0.2):
    """
    Calculates the optimal stake using the Kelly Criterion.
    
    Formula: f* = (bp - q) / b
    where:
    - b is the net odds (decimal odds - 1)
    - p is the probability of winning (Fair Prob)
    - q is the probability of losing (1 - p)
    
    multiplier: Fractional Kelly factor to reduce volatility (default 0.2 for 20% Kelly)
    """
    if odds <= 1.0:
        return 0.0
        
    b = odds - 1
    p = fair_prob
    q = 1.0 - p
    
    # Raw Kelly Fraction
    kelly_f = (b * p - q) / b
    
    # Apply fractional multiplier and clamp to positive
    fractional_kelly = max(0.0, kelly_f * multiplier)
    
    bankroll = 40.00
    stake = fractional_kelly * bankroll
    
    # Cap the absolute maximum stake on any single bet to $2.00
    return round(min(stake, 2.00), 2)
