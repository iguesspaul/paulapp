import json

class CasinoParser:
    def __init__(self):
        pass

    def extract_markets(self, file_path):
        """
        Parses the JSON file from the Altenar API and returns a structured list of markets.
        Format: [{'name': 'Market Name', 'selections': [{'name': '1:0', 'price': 5.5}, ...]}]
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print("Failed to decode JSON from file")
                return []
        
        results = []
        odds_list = data.get('odds', [])
        
        # Create a quick lookup map for odds by their ID
        odds_map = {odd['id']: odd for odd in odds_list}

        for market in data.get('markets', []):
            market_name = market.get('name', 'Unknown Market')
            
            # Include score-based, HT/FT, BTTS, and Total/Over-Under markets
            m_lower = market_name.lower()
            if "score" not in m_lower and "ht/ft" not in m_lower and \
               "both teams to score" not in m_lower and "total" not in m_lower and \
               "over/under" not in m_lower:
                continue
                
            market_data = {
                'name': market_name,
                'selections': []
            }
            
            # Extract the nested list of odd IDs
            odd_ids = []
            for id_group in market.get('desktopOddIds', []):
                for odd_id in id_group:
                    odd_ids.append(odd_id)
            
            for odd_id in odd_ids:
                odd = odds_map.get(odd_id)
                if odd:
                    name = odd.get('name')
                    price = odd.get('price')
                    
                    if name and price:
                        market_data['selections'].append({
                            'name': str(name),
                            'price': float(price)
                        })
            
            if market_data['selections']:
                results.append(market_data)
        
        return results
