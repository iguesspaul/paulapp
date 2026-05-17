import urllib.request
import json
import asyncio
from datetime import datetime, timedelta
from src.core.config import ALTENAR_BASE_URL, ALTENAR_COMMON_PARAMS

def fetch_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read())
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

async def find_matches(champ_id: int):
    """
    Finds all upcoming matches for a specific championship ID.
    Only includes matches that are not live and are scheduled within the next 48 hours.
    """
    url = f"{ALTENAR_BASE_URL}/GetBreadcrumbEvents?{ALTENAR_COMMON_PARAMS}&champId={champ_id}&isLive=false"
    data = fetch_json(url)
    matches = []

    if data and 'events' in data:
        current_time = datetime.utcnow()
        # Set cutoff to 48 hours from now
        cutoff_time = current_time + timedelta(hours=48)

        for event in data['events']:
            # Check if event has a start time field
            start_time_str = event.get('startTime') or event.get('start') or event.get('startDate')

            # If we have a start time, check if it's within our window
            if start_time_str:
                try:
                    # Try to parse the start time
                    # Handle different time formats that might be returned
                    if isinstance(start_time_str, str):
                        # Try ISO format first
                        if 'T' in start_time_str:
                            event_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                        else:
                            # Try other common formats
                            event_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
                    elif isinstance(start_time_str, (int, float)):
                        # Assume it's a Unix timestamp
                        event_time = datetime.utcfromtimestamp(start_time_str)
                    else:
                        # If we can't parse it, include the match (better to include than exclude)
                        event_time = current_time

                    # Only include matches that are in the future and within our cutoff
                    if current_time <= event_time <= cutoff_time:
                        details_url = f"{ALTENAR_BASE_URL}/GetEventDetails?{ALTENAR_COMMON_PARAMS}&eventId={event['id']}&showNonBoosts=false"
                        matches.append({
                            "id": event['id'],
                            "name": event['name'],
                            "details_url": details_url,
                            "start_time": event_time.isoformat()
                        })
                except (ValueError, TypeError):
                    # If we can't parse the time, include the match to be safe
                    details_url = f"{ALTENAR_BASE_URL}/GetEventDetails?{ALTENAR_COMMON_PARAMS}&eventId={event['id']}&showNonBoosts=false"
                    matches.append({
                        "id": event['id'],
                        "name": event['name'],
                        "details_url": details_url
                    })
            else:
                # If no start time is provided, include the match (assume it's upcoming)
                details_url = f"{ALTENAR_BASE_URL}/GetEventDetails?{ALTENAR_COMMON_PARAMS}&eventId={event['id']}&showNonBoosts=false"
                matches.append({
                    "id": event['id'],
                    "name": event['name'],
                    "details_url": details_url
                })

    # Sort matches by start time if available, putting matches without start times last
    matches.sort(key=lambda x: x.get('start_time', '9999'))

    return matches

async def fetch_page_json(url: str, output_path: str):
    """
    Fetches the JSON from the Altenar API and saves it.
    """
    data = fetch_json(url)
    if data:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    return False

def make_slug(s):
    import re
    s = s.lower().strip()
    s = re.sub(r'[^a-z0-9\s-]', '', s)
    s = re.sub(r'[\s-]+', '-', s)
    return s

async def discover_active_leagues():
    """
    Dynamically discovers all active soccer championships with prelive events from the Altenar menu.
    """
    menu_url = f"{ALTENAR_BASE_URL}/GetClickableSportMenu?{ALTENAR_COMMON_PARAMS}&period=0"
    menu = fetch_json(menu_url)
    if not menu:
        return []
        
    sports = menu.get("sports", [])
    soccer_sport = None
    for s in sports:
        if s.get("id") == 66 or "football" in s.get("name", "").lower() or "soccer" in s.get("name", "").lower():
            soccer_sport = s
            break
            
    if not soccer_sport:
        return []
        
    soccer_cat_ids = set(soccer_sport.get("catIds", []))
    categories = menu.get("categories", [])
    champs = menu.get("champs", [])
    champs_map = {c["id"]: c for c in champs}
    
    extracted_leagues = []
    for cat in categories:
        if cat.get("id") in soccer_cat_ids:
            cat_name = cat.get("name", "Unknown Country")
            for champ_id in cat.get("champIds", []):
                champ = champs_map.get(champ_id)
                if champ:
                    champ_name = champ.get("name", "Unknown League")
                    events_count = champ.get("eventsCount", 0)
                    if events_count > 0:
                        country_slug = make_slug(cat_name)
                        league_slug = make_slug(champ_name)
                        
                        # Generate normalized paths
                        if league_slug == "laliga":
                            be_path = f"soccer/{country_slug}/laliga"
                            pin_path = f"{country_slug}-la-liga"
                        else:
                            be_path = f"soccer/{country_slug}/{league_slug}"
                            pin_path = f"{country_slug}-{league_slug}"
                            
                        extracted_leagues.append({
                            "name": champ_name,
                            "country": cat_name,
                            "champ_id": champ_id,
                            "be_path": be_path,
                            "pin_path": pin_path,
                            "events_count": events_count
                        })
                        
    # Sort leagues by events count descending to prioritize highly active leagues
    extracted_leagues.sort(key=lambda x: x["events_count"], reverse=True)
    return extracted_leagues