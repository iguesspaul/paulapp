import re
import math
from scipy.stats import poisson

class MarketResolver:
    def __init__(self, prob_grid):
        self.prob_grid = prob_grid
        self.grid = prob_grid.grid
        self.h1_grid = prob_grid.h1_grid
        self.h2_grid = prob_grid.h2_grid

    def _get_active_grid(self, market_name):
        """
        Get the appropriate probability grid based on market type.
        Ensures 1st Half markets use the Half-Time Lambda (45% of total).
        """
        if "1st half" in market_name.lower() or "1st/2nd half" in market_name.lower():
            return self.h1_grid
        elif "2nd half" in market_name.lower():
            return self.h2_grid
        return self.grid

    def resolve(self, market_name, selection_name):
        market_name = market_name.lower()
        selection_name = selection_name.lower()
        
        # Strict guardrail: only price goals
        for forbidden in ['corner', 'booking', 'card', 'shot']:
            if forbidden in market_name:
                return None
                
        active_grid = self._get_active_grid(market_name)
        
        # Halftime/fulltime correct score (1:2 1:2)
        if "halftime/fulltime correct score" in market_name:
            scores = re.findall(r'(\d+)\s*[:\-]\s*(\d+)', selection_name)
            if len(scores) == 2:
                h1, a1 = int(scores[0][0]), int(scores[0][1])
                hf, af = int(scores[1][0]), int(scores[1][1])
                h2 = hf - h1
                a2 = af - a1
                if h1 < 7 and a1 < 7 and h2 >= 0 and a2 >= 0 and h2 < 7 and a2 < 7:
                    return self.h1_grid[h1][a1] * self.h2_grid[h2][a2]
            return 0.0

        # 1st/2nd half both teams to score (Yes/no)
        if "1st/2nd half both teams to score" in market_name:
            parts = selection_name.split('/')
            if len(parts) == 2:
                h1_yes = "yes" in parts[0]
                h2_yes = "yes" in parts[1]
                prob1 = 0.0
                prob2 = 0.0
                for h in range(7):
                    for a in range(7):
                        if h1_yes and h > 0 and a > 0: prob1 += self.h1_grid[h][a]
                        elif not h1_yes and (h == 0 or a == 0): prob1 += self.h1_grid[h][a]
                        
                        if h2_yes and h > 0 and a > 0: prob2 += self.h2_grid[h][a]
                        elif not h2_yes and (h == 0 or a == 0): prob2 += self.h2_grid[h][a]
                return prob1 * prob2
            return 0.0

        # 1x2 & both teams to score
        # Calculates the probability of BOTH occurring (Win * BTTS), not just one
        if "1x2" in market_name and "both teams to score" in market_name:
            is_yes = "yes" in selection_name
            is_draw = "draw" in selection_name or "x &" in selection_name
            is_away = "2 &" in selection_name or ("away" in selection_name)
            is_home = "1 &" in selection_name or ("home" in selection_name) or (not is_draw and not is_away and "&" in selection_name)

            prob = 0.0
            for h in range(7):
                for a in range(7):
                    # BTTS condition: both teams must score (h > 0 and a > 0) for YES
                    #                 at least one team doesn't score (h == 0 or a == 0) for NO
                    btts = (h > 0 and a > 0) if is_yes else (h == 0 or a == 0)

                    # Match result condition
                    match_win = False
                    if is_home and h > a: match_win = True
                    elif is_away and a > h: match_win = True
                    elif is_draw and h == a: match_win = True

                    # Only count probability when BOTH conditions are met
                    if btts and match_win:
                        prob += active_grid[h][a]
            return prob

        # Double chance & both teams to score
        if "double chance" in market_name and "both teams to score" in market_name:
            is_yes = "yes" in selection_name
            dc_1x = "1x" in selection_name or "1/x" in selection_name
            dc_x2 = "x2" in selection_name or "x/2" in selection_name
            dc_12 = "12" in selection_name or "1/2" in selection_name
            
            prob = 0.0
            for h in range(7):
                for a in range(7):
                    btts = (h > 0 and a > 0) if is_yes else (h == 0 or a == 0)
                    match_win = False
                    if dc_1x and h >= a: match_win = True
                    elif dc_x2 and a >= h: match_win = True
                    elif dc_12 and h != a: match_win = True
                    
                    if btts and match_win:
                        prob += active_grid[h][a]
            return prob

        # Both Teams To Score (Pure)
        if ("both teams to score" in market_name or "btts" in market_name) and "1x2" not in market_name and "double chance" not in market_name:
            if "yes" in selection_name:
                prob = 0.0
                for h in range(1, 7):
                    for a in range(1, 7):
                        prob += active_grid[h][a]
                return prob
            elif "no" in selection_name:
                prob = 0.0
                for h in range(7):
                    for a in range(7):
                        if h == 0 or a == 0:
                            prob += active_grid[h][a]
                return prob

        # Multiscores (e.g., "1:0, 2:0 or 3:0")
        if "multiscore" in market_name or "or" in selection_name or "," in selection_name:
            scores = re.findall(r'(\d+)\s*[:\-]\s*(\d+)', selection_name)
            if scores:
                prob = 0.0
                for score in scores:
                    h, a = int(score[0]), int(score[1])
                    if h < 7 and a < 7:
                        prob += active_grid[h][a]
                return prob
                
        # Correct Score
        score_match = re.search(r'(\d+)\s*[:\-]\s*(\d+)', selection_name)
        if "score" in market_name and score_match:
            h = int(score_match.group(1))
            a = int(score_match.group(2))
            if h < 7 and a < 7:
                return active_grid[h][a]
            return 0.0

        # Total Over/Under
        if "total" in market_name or "over/under" in market_name or "over" in market_name:
            if "1st half" in market_name:
                active_lambda = self.prob_grid.h1_lambda + self.prob_grid.a1_lambda
            elif "2nd half" in market_name:
                active_lambda = self.prob_grid.h2_lambda + self.prob_grid.a2_lambda
            else:
                active_lambda = self.prob_grid.match_lambda

            over_match = re.search(r'over\s*(\d+\.?\d*)', selection_name)
            if over_match:
                n = float(over_match.group(1))
                return float(poisson.sf(math.floor(n), active_lambda))
                
            under_match = re.search(r'under\s*(\d+\.?\d*)', selection_name)
            if under_match:
                n = float(under_match.group(1))
                return float(poisson.cdf(math.floor(n), active_lambda))

        # Winning Margin
        if "margin" in market_name:
            side = None
            if "home" in selection_name or "1" in selection_name:
                side = "home"
            elif "away" in selection_name or "2" in selection_name:
                side = "away"
                
            margin_match = re.search(r'by\s*(\d+)', selection_name)
            if side and margin_match:
                n = int(margin_match.group(1))
                prob = 0.0
                for h in range(7):
                    for a in range(7):
                        if side == "home" and (h - a) == n:
                            prob += active_grid[h][a]
                        elif side == "away" and (a - h) == n:
                            prob += active_grid[h][a]
                return prob

        # Draw
        if "draw" in selection_name or "x" == selection_name.strip():
            prob = 0.0
            for h in range(7):
                prob += active_grid[h][h]
            return prob

        # Match Winner (1x2)
        if "1x2" in market_name or "match winner" in market_name:
            if "1" == selection_name.strip() or "home" in selection_name:
                prob = 0.0
                for h in range(7):
                    for a in range(7):
                        if h > a: prob += active_grid[h][a]
                return prob
            elif "2" == selection_name.strip() or "away" in selection_name:
                prob = 0.0
                for h in range(7):
                    for a in range(7):
                        if a > h: prob += active_grid[h][a]
                return prob
        
        return 0.0
