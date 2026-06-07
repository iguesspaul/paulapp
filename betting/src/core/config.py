# League mappings between Casino (Altenar) and Sharp (BetExplorer)
LEAGUES = [
    {
        "name": "Premier League",
        "country": "England",
        "champ_id": 2936,
        "be_path": "soccer/england/premier-league",
        "pin_path": "england-premier-league",
    },
    {
        "name": "LaLiga",
        "country": "Spain",
        "champ_id": 2941,
        "be_path": "soccer/spain/laliga",
        "pin_path": "spain-la-liga",
    },
    {
        "name": "Serie A",
        "country": "Italy",
        "champ_id": 2942,
        "be_path": "soccer/italy/serie-a",
        "pin_path": "italy-serie-a",
    },
    {
        "name": "Bundesliga",
        "country": "Germany",
        "champ_id": 2950,
        "be_path": "soccer/germany/bundesliga",
        "pin_path": "germany-bundesliga",
    },
]

# Bankroll Management
INITIAL_BANKROLL = 5000.0
KELLY_MULTIPLIER = 0.20  # Conservative "Fractional Kelly"

# Altenar API Base URL params
ALTENAR_BASE_URL = "https://sb2frontend-altenar2.biahosted.com/api/widget"
ALTENAR_COMMON_PARAMS = "culture=en-GB&timezoneOffset=300&integration=justbetjaonline&deviceType=1&numFormat=en-GB&countryCode=JM"
