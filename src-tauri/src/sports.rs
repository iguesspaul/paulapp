use crate::models::{StandingsResponse, TeamStanding};
use reqwest::Client;

const SOFASCORE_BASE: &str = "https://api.sofascore.com/api/v1";

fn build_client() -> Client {
    reqwest::Client::builder()
        .user_agent("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        .default_headers({
            let mut headers = reqwest::header::HeaderMap::new();
            headers.insert("Accept", "application/json".parse().unwrap());
            headers.insert("Accept-Language", "en-US,en;q=0.9".parse().unwrap());
            headers.insert("Referer", "https://www.sofascore.com/".parse().unwrap());
            headers.insert("Origin", "https://www.sofascore.com".parse().unwrap());
            headers
        })
        .build()
        .unwrap()
}

async fn get_season_id(client: &Client, tournament_id: &str) -> Result<u32, String> {
    let url = format!(
        "{}/unique-tournament/{}/seasons",
        SOFASCORE_BASE, tournament_id
    );
    eprintln!("[sports] GET {}", url);

    let raw = client
        .get(&url)
        .send()
        .await
        .map_err(|e| format!("season request failed: {}", e))?
        .text()
        .await
        .map_err(|e| format!("season body read failed: {}", e))?;

    eprintln!("[sports] season raw: {}", &raw[..500.min(raw.len())]);

    let json: serde_json::Value = serde_json::from_str(&raw).map_err(|e| {
        format!(
            "season json parse failed: {}\nraw: {}",
            e,
            &raw[..200.min(raw.len())]
        )
    })?;

    json["seasons"][0]["id"]
        .as_u64()
        .map(|id| id as u32)
        .ok_or_else(|| format!("no season id in response: {}", &raw[..200.min(raw.len())]))
}

pub async fn fetch_standings(league_id: &str) -> Result<StandingsResponse, String> {
    eprintln!("[sports] fetch_standings called: {}", league_id);

    let client = build_client();
    let season_id = get_season_id(&client, league_id).await?;

    eprintln!("[sports] season_id: {}", season_id);

    let url = format!(
        "{}/unique-tournament/{}/season/{}/standings/total",
        SOFASCORE_BASE, league_id, season_id
    );

    eprintln!("[sports] GET {}", url);

    let raw = client
        .get(&url)
        .send()
        .await
        .map_err(|e| format!("standings request failed: {}", e))?
        .text()
        .await
        .map_err(|e| format!("standings body read failed: {}", e))?;

    eprintln!("[sports] standings raw: {}", &raw[..500.min(raw.len())]);

    let json: serde_json::Value = serde_json::from_str(&raw).map_err(|e| {
        format!(
            "standings json parse failed: {}\nraw: {}",
            e,
            &raw[..200.min(raw.len())]
        )
    })?;

    let rows = json["standings"][0]["rows"].as_array().ok_or_else(|| {
        format!(
            "no standings rows in response: {}",
            &raw[..200.min(raw.len())]
        )
    })?;

    let standings: Vec<TeamStanding> = rows
        .iter()
        .map(|row| {
            let goals_for = row["scoresFor"].as_u64().unwrap_or(0) as u32;
            let goals_against = row["scoresAgainst"].as_u64().unwrap_or(0) as u32;
            TeamStanding {
                position: row["position"].as_u64().unwrap_or(0) as u32,
                team_id: row["team"]["id"].as_u64().unwrap_or(0) as u32,
                team_name: row["team"]["name"].as_str().unwrap_or("").to_string(),
                short_name: row["team"]["shortName"].as_str().unwrap_or("").to_string(),
                played: row["matches"].as_u64().unwrap_or(0) as u32,
                won: row["wins"].as_u64().unwrap_or(0) as u32,
                drawn: row["draws"].as_u64().unwrap_or(0) as u32,
                lost: row["losses"].as_u64().unwrap_or(0) as u32,
                goals_for,
                goals_against,
                goal_difference: goals_for as i32 - goals_against as i32,
                points: row["points"].as_u64().unwrap_or(0) as u32,
            }
        })
        .collect();

    eprintln!("[sports] parsed {} rows", standings.len());

    Ok(StandingsResponse {
        league_id: league_id.to_string(),
        season_id,
        standings,
        cached_at: 0,
    })
}

pub async fn fetch_upcoming_matches(
    league_id: &str,
) -> Result<crate::models::UpcomingMatchesResponse, String> {
    use crate::models::{UpcomingMatch, UpcomingMatchesResponse};

    eprintln!("[sports] fetch_upcoming_matches called: {}", league_id);

    let client = build_client();
    let season_id = get_season_id(&client, league_id).await?;

    eprintln!("[sports] season_id: {}", season_id);

    let url = format!(
        "{}/unique-tournament/{}/season/{}/events/next/0",
        SOFASCORE_BASE, league_id, season_id
    );

    eprintln!("[sports] GET {}", url);

    let raw = client
        .get(&url)
        .send()
        .await
        .map_err(|e| format!("matches request failed: {}", e))?
        .text()
        .await
        .map_err(|e| format!("matches body read failed: {}", e))?;

    eprintln!("[sports] matches raw: {}", &raw[..500.min(raw.len())]);

    let json: serde_json::Value = serde_json::from_str(&raw).map_err(|e| {
        format!(
            "matches json parse failed: {}\nraw: {}",
            e,
            &raw[..200.min(raw.len())]
        )
    })?;

    let events = json["events"]
        .as_array()
        .ok_or_else(|| format!("no events in response: {}", &raw[..200.min(raw.len())]))?;

    let matches: Vec<UpcomingMatch> = events
        .iter()
        .take(4)
        .map(|event| UpcomingMatch {
            event_id: event["id"].as_u64().unwrap_or(0),
            slug: event["slug"].as_str().unwrap_or("").to_string(),
            round: event["roundInfo"]["round"].as_u64().unwrap_or(0) as u32,
            start_timestamp: event["startTimestamp"].as_u64().unwrap_or(0),
            status: event["status"]["type"]
                .as_str()
                .unwrap_or("unknown")
                .to_string(),
            home_team_id: event["homeTeam"]["id"].as_u64().unwrap_or(0) as u32,
            home_team_name: event["homeTeam"]["name"].as_str().unwrap_or("").to_string(),
            away_team_id: event["awayTeam"]["id"].as_u64().unwrap_or(0) as u32,
            away_team_name: event["awayTeam"]["name"].as_str().unwrap_or("").to_string(),
        })
        .collect();

    eprintln!("[sports] parsed {} matches", matches.len());

    Ok(UpcomingMatchesResponse {
        league_id: league_id.to_string(),
        season_id,
        matches,
    })
}
