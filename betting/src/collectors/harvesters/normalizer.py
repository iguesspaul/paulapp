"""
Shared team name normalization utilities for Pinnacle and BetExplorer harvesters.
"""

import re
import unicodedata

# Common club suffixes that carry no identifying information
_STRIP_SUFFIXES = {
    "fc",
    "cf",
    "sc",
    "ac",
    "bv",
    "sv",
    "rv",
    "fk",
    "sk",
    "rfc",
    "afc",
    "united",
    "utd",
    "city",
    "town",
    "athletic",
    "atletico",
    "sporting",
    "wanderers",
    "rovers",
    "rangers",
    "county",
    "hotspur",
    "wednesday",
    "albion",
    "villa",
    "palace",
}

# League name alias table — maps Altenar names to what each sharp platform uses.
# Key format: (altenar_league_slug, country_slug or "")
# The league_slug is the last segment of be_path (e.g. 'international-friendly-games')
# Entries are added as name-mismatch failures are discovered during harvesting.
#
# Fields:
#   betexplorer_search  — preferred search term for BetExplorer's search API
#                          (overrides the raw league name)
#   pinnacle_name       — exact league name Pinnacle uses (for exact match bypassing
#                          the token-set intersection scoring)
LEAGUE_ALIASES: dict = {
    # World
    ("international-friendly-games", "world"): {
        "betexplorer_search": "Friendly International",
        "pinnacle_name": "International - Friendlies",
    },
    ("int-friendly-games-women", "world"): {
        "betexplorer_search": "Friendly International Women",
        "pinnacle_name": "International - Friendlies Women",
    },
    ("world-cup-2026", "world"): {
        "betexplorer_search": "World Cup",
        "pinnacle_name": "FIFA - World Cup",
    },
    ("u20-friendly-games", "world"): {
        "betexplorer_search": "Friendly International U20",
        "pinnacle_name": "International - Friendlies U20",
    },
    ("u21-friendly-games", "world"): {
        "betexplorer_search": "Friendly International U21",
        "pinnacle_name": "International - Friendlies U21",
    },
    ("u23-friendly-games", "world"): {
        "betexplorer_search": "Friendly International U23",
        "pinnacle_name": "International - Friendlies U23",
    },
    # Russia
    ("russian-second-league", "russia"): {
        "betexplorer_search": "FNL 2",
        # Pinnacle does not offer Russian lower divisions — coverage gap
    },
    # Brazil — BetExplorer uses different names than Altenar
    ("brasileiro-serie-a", "brazil"): {
        "betexplorer_search": "Serie A Betano",
    },
    ("brasileiro-serie-b", "brazil"): {
        "betexplorer_search": "Serie B",
    },
    ("brasileiro-serie-c", "brazil"): {
        "betexplorer_search": "Serie C",
    },
    ("brasileiro-serie-d", "brazil"): {
        "betexplorer_search": "Serie D",
    },
    ("copa-do-brasil", "brazil"): {
        "betexplorer_search": "Copa do Brasil",
    },
    ("paulista-segunda-divisao", "brazil"): {
        "betexplorer_search": "Paulista Serie B",
    },
    # Poland
    ("iv-liga", "poland"): {
        "betexplorer_search": "4 Liga",
    },
    ("ii-liga", "poland"): {
        "betexplorer_search": "2 Liga",
        "pinnacle_name": "Poland - 2nd Liga",
    },
    # Sweden
    ("div-1", "sweden"): {
        "betexplorer_search": "Division 1 Norra",
        "pinnacle_name": "Sweden - Division 1 Norra",
    },
    # Austria
    ("austrian-landesliga", "austria"): {
        "betexplorer_search": "Regionalliga",
    },
    # Ecuador
    ("ligapro-serie-a", "ecuador"): {
        "betexplorer_search": "Liga Pro",
        "pinnacle_name": "Ecuador - Serie A",
    },
    # Vietnam — BetExplorer uses different hyphenation
    ("v-league-2", "vietnam"): {
        "betexplorer_search": "V League 2",
        "pinnacle_name": "Vietnam - V League 2",
    },
    # Japan — "J2/J3 League" on BetExplorer vs "J2J3 League" from Altenar
    ("j2j3-league", "japan"): {
        "betexplorer_search": "J2 J3 League",
    },
    ("jleague", "japan"): {
        "betexplorer_search": "J League",
    },
    ("regional-football-leagues", "japan"): {
        "betexplorer_search": "Regional League",
    },
    # Cameroon — women's league may be under different name
    ("national-championship-women", "cameroon"): {
        "betexplorer_search": "Championship Women",
    },
    # Republic of Korea
    ("k-league-2", "republic-of-korea"): {
        "betexplorer_search": "K League 2",
        "pinnacle_name": "Korea Republic - K League 2",
    },
    ("korea-republic-k4-league", "republic-of-korea"): {
        "betexplorer_search": "K4 League",
        "pinnacle_name": "Korea Republic - K4 League",
    },
    # New Zealand — BetExplorer calls it "Football Championship"
    ("premiership", "new-zealand"): {
        "betexplorer_search": "Football Championship",
        # Pinnacle has Central/Northern/Southern regional leagues (different competition)
    },
    # Paraguay
    ("primera-division-b-apf", "paraguay"): {
        "betexplorer_search": "Primera B",
    },
    # Uruguay
    ("primera-division-amateur", "uruguay"): {
        "betexplorer_search": "Primera Amateur",
    },
    # Chile
    ("primera-division", "chile"): {
        "pinnacle_name": "Chile - Primera Division",
        "betexplorer_search": "Primera Division",
    },
    ("primera-b", "chile"): {
        "pinnacle_name": "Chile - Primera B",
    },
    ("segunda-division", "chile"): {
        "pinnacle_name": "Chile - Segunda Division",
    },
    ("tercera-division", "chile"): {
        "pinnacle_name": "Chile - Tercera Division A",
    },
    ("league-cup", "chile"): {
        "pinnacle_name": "Chile - League Cup",
    },
    # Colombia
    ("primera-a-colombia", "colombia"): {
        "betexplorer_search": "Primera A",
    },
    # Ecuador
    ("ligapro-primera-b", "ecuador"): {
        "betexplorer_search": "Serie B",
        "pinnacle_name": "Ecuador - Serie B",
    },
    # Hungary — cups may use different names
    ("u19-league", "hungary"): {
        "betexplorer_search": "U19",
    },
    # Iceland
    ("1st-deild", "iceland"): {
        "betexplorer_search": "1 Deild",
    },
    ("2-deild", "iceland"): {
        "betexplorer_search": "2 Deild",
    },
    ("3-deild", "iceland"): {
        "betexplorer_search": "3 Deild",
    },
    ("5-deild-karla", "iceland"): {
        "betexplorer_search": "5 Deild",
    },
    # Ireland
    ("premier-division", "ireland"): {
        "pinnacle_name": "Ireland - Premier",
    },
    ("first-division", "ireland"): {
        "pinnacle_name": "Ireland - Division 1",
    },
    # Finland
    ("ykkonen", "finland"): {
        "pinnacle_name": "Finland - Ykkonen",
    },
    ("ykkosliiga", "finland"): {
        "pinnacle_name": "Finland - Ykkosliiga",
    },
    ("veikkausliiga", "finland"): {
        "pinnacle_name": "Finland - Veikkausliiga",
    },
    ("kolmonen", "finland"): {
        "betexplorer_search": "Kolmonen",
    },
    ("kakkonen", "finland"): {
        "betexplorer_search": "Kakkonen",
    },
    # Denmark
    ("2nd-division", "denmark"): {
        "pinnacle_name": "Denmark - 2nd Division",
    },
    ("3rd-division", "denmark"): {
        "pinnacle_name": "Denmark - 3rd Division",
    },
    ("danmarksserien", "denmark"): {
        "pinnacle_name": "Denmark - Denmark Series",
    },
    # Uruguay
    ("primera-division", "uruguay"): {
        "pinnacle_name": "Uruguay - Primera Division",
    },
    ("segunda-division", "uruguay"): {
        "pinnacle_name": "Uruguay - Segunda Division",
    },
    # Argentina
    ("copa-argentina", "argentina"): {
        "pinnacle_name": "Argentina - Cup",
    },
    ("primera-b", "argentina"): {
        "pinnacle_name": "Argentina - Primera B Metropolitana",
    },
    ("primera-nacional", "argentina"): {
        "pinnacle_name": "Argentina - Primera B Nacional",
    },
    # Norway
    ("1st-division", "norway"): {
        "pinnacle_name": "Norway - 1st Division",
    },
    ("eliteserien", "norway"): {
        "betexplorer_search": "Eliteserien",
    },
    ("nm-cup", "norway"): {
        "pinnacle_name": "Norway - Cup",
    },
    ("3rd-division", "norway"): {
        "pinnacle_name": "Norway - 3rd Division",
    },
    # Poland
    # Spain
    ("primera-federacion", "spain"): {
        "pinnacle_name": "Spain - Primera Federacion",
    },
    ("laliga-2", "spain"): {
        "pinnacle_name": "Spain - Segunda Division",
    },
    ("tercera-division", "spain"): {
        "pinnacle_name": "Spain - Tercera Division",
    },
    # Sweden
    ("superettan", "sweden"): {
        "pinnacle_name": "Sweden - Superettan",
    },
    ("division-2", "sweden"): {
        "pinnacle_name": "Sweden - 2nd Division",
    },
    # Netherlands
    ("tweede-divisie", "netherlands"): {
        "pinnacle_name": "Netherlands - Tweede Divisie",
    },
    # Switzerland
    ("erste-liga", "switzerland"): {
        "betexplorer_search": "1 Liga",
    },
    ("u19-elite", "switzerland"): {
        "pinnacle_name": "Switzerland - U19 Elite",
    },
    # USA
    ("usl-championship", "usa"): {
        "pinnacle_name": "USA - USL Championship",
    },
    ("usl-league-two", "usa"): {
        "pinnacle_name": "USA - USL League 2",
    },
    ("mls-next-pro", "usa"): {
        "pinnacle_name": "USA - MLS Next Pro League",
    },
    ("womens-premier-soccer-league", "usa"): {
        "pinnacle_name": "USA - Women Premier Soccer League",
    },
    ("mls", "usa"): {
        "betexplorer_search": "MLS",
    },
    # Canada
    ("canadian-premier-league", "canada"): {
        "pinnacle_name": "Canada - Premier League",
    },
    # Vietnam
    # South Africa
    ("premiership", "south-africa"): {
        "pinnacle_name": "South Africa - PSL",
    },
    # UEFA
    ("uefa-champions-league", "europe"): {
        "pinnacle_name": "UEFA - Champions League",
    },
    ("uefa-nations-league", "europe"): {
        "betexplorer_search": "Nations League",
    },
    ("european-u19-championship-qualification", "europe"): {
        "pinnacle_name": "UEFA - U19 Euro Championship Qualifiers",
    },
}


def normalize(name: str) -> str:
    """
    Lowercase, strip accents, remove punctuation, remove common club suffixes.
    Returns a space-joined string of meaningful tokens.
    """
    # Unicode accent stripping
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_str = nfkd.encode("ascii", "ignore").decode("ascii")
    # Lowercase and remove non-alphanumeric (keep spaces)
    cleaned = re.sub(r"[^a-z0-9\s]", " ", ascii_str.lower())
    tokens = cleaned.split()
    # Remove pure suffix tokens (keep them if it's the whole name)
    filtered = [t for t in tokens if t not in _STRIP_SUFFIXES] or tokens
    return " ".join(filtered)


def normalize_slug(slug: str) -> str:
    """
    Normalize a URL slug (e.g. 'england-premier-league') into a comparable string.
    Replaces hyphens/underscores with spaces, then applies normalize().
    """
    return normalize(slug.replace("-", " ").replace("_", " "))


def token_set(s: str) -> set:
    """Return the set of word tokens from a normalized string."""
    return set(normalize(s).split())


def name_match_score(a: str, b: str) -> float:
    """
    Word-set intersection score: |A ∩ B| / max(|A|, |B|).
    More robust than SequenceMatcher on full strings because it ignores
    word order and unimportant suffix words.
    Returns 0.0-1.0; higher is better.
    """
    ta = token_set(a)
    tb = token_set(b)
    if not ta or not tb:
        return 0.0
    intersection = len(ta & tb)
    return intersection / max(len(ta), len(tb))


def american_to_decimal(american: int | float) -> float:
    """Convert American odds to decimal odds."""
    if american > 0:
        return round(american / 100 + 1, 4)
    else:
        return round(100 / abs(american) + 1, 4)


def get_alias(league_slug: str, country_slug: str = "") -> dict | None:
    """
    Look up league aliases for the given league and country.
    Returns the alias dict or None if no alias exists.
    """
    return LEAGUE_ALIASES.get((league_slug, country_slug))


def make_slug(s: str) -> str:
    """Convert a string to a URL-safe slug (compatible with scraper.make_slug)."""
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s-]+", "-", s)
    return s
