use crate::models::{SleepScore, WhoopToken};
use chrono::Utc;
use once_cell::sync::Lazy;
use reqwest::Client;
use std::fs;
use std::path::PathBuf;
use std::sync::Mutex;

static WHOOP_TOKEN: Lazy<Mutex<Option<WhoopToken>>> = Lazy::new(|| Mutex::new(None));

const WHOOP_AUTH_URL: &str = "https://api.prod.whoop.com/oauth/oauth2/auth";
const WHOOP_TOKEN_URL: &str = "https://api.prod.whoop.com/oauth/oauth2/token";
const WHOOP_API_BASE: &str = "https://api.prod.whoop.com/developer/v2";

fn get_token_path() -> PathBuf {
    dirs::config_dir()
        .unwrap_or_else(|| PathBuf::from("."))
        .join("paulapp")
        .join("whoop_token.json")
}

fn load_token() -> Option<WhoopToken> {
    let mut cache = WHOOP_TOKEN.lock().unwrap();
    if cache.is_some() {
        return cache.clone();
    }

    if let Ok(data) = fs::read_to_string(get_token_path()) {
        if let Ok(token) = serde_json::from_str::<WhoopToken>(&data) {
            *cache = Some(token.clone());
            return Some(token);
        }
    }
    None
}

fn save_token(token: WhoopToken) {
    let mut cache = WHOOP_TOKEN.lock().unwrap();
    *cache = Some(token.clone());

    let _ = fs::write(
        get_token_path(),
        serde_json::to_string(&token).unwrap_or_default(),
    );
}

pub fn get_auth_url() -> Result<String, String> {
    dotenvy::dotenv().ok();
    let client_id = std::env::var("WHOOP_API_PUBLIC").map_err(|_| "WHOOP_API_PUBLIC missing")?;

    // Scopes needed for sleep data
    let scopes = "offline read:sleep read:recovery read:cycles read:workout read:profile";
    let redirect_uri = "http://localhost:1420/callback";

    let url = format!(
        "{}?client_id={}&redirect_uri={}&response_type=code&scope={}&state=auth_whoop",
        WHOOP_AUTH_URL,
        client_id,
        redirect_uri,
        urlencoding::encode(scopes)
    );
    Ok(url)
}

pub async fn exchange_token(code: String) -> Result<(), String> {
    dotenvy::dotenv().ok();
    let client_id = std::env::var("WHOOP_API_PUBLIC").map_err(|_| "WHOOP_API_PUBLIC missing")?;
    let client_secret =
        std::env::var("WHOOP_API_SECRET").map_err(|_| "WHOOP_API_SECRET missing")?;

    let client = Client::new();
    let params = [
        ("grant_type", "authorization_code"),
        ("code", &code),
        ("client_id", &client_id),
        ("client_secret", &client_secret),
        ("redirect_uri", "http://localhost:1420/callback"),
    ];

    eprintln!("[whoop] Exchanging code for token...");

    let res = client
        .post(WHOOP_TOKEN_URL)
        .form(&params)
        .send()
        .await
        .map_err(|e| format!("Token request failed: {}", e))?;

    let status = res.status();
    let text = res.text().await.unwrap_or_default();

    if !status.is_success() {
        return Err(format!("Failed to exchange token: {} - {}", status, text));
    }

    let mut token: WhoopToken = serde_json::from_str(&text)
        .map_err(|e| format!("Failed to parse token response: {}", e))?;

    token.expires_at = Some(Utc::now().timestamp() as u64 + token.expires_in);
    save_token(token);

    Ok(())
}

async fn refresh_token_if_needed() -> Result<WhoopToken, String> {
    let token = load_token().ok_or_else(|| "Not authenticated with WHOOP".to_string())?;

    let now = Utc::now().timestamp() as u64;
    let expires_at = token.expires_at.unwrap_or(0);

    // Refresh if expiring within 5 minutes
    if now + 300 < expires_at {
        return Ok(token);
    }

    dotenvy::dotenv().ok();
    let client_id = std::env::var("WHOOP_API_PUBLIC").map_err(|_| "WHOOP_API_PUBLIC missing")?;
    let client_secret =
        std::env::var("WHOOP_API_SECRET").map_err(|_| "WHOOP_API_SECRET missing")?;

    eprintln!("[whoop] Refreshing token...");

    let client = Client::new();
    let params = [
        ("grant_type", "refresh_token"),
        ("refresh_token", &token.refresh_token),
        ("client_id", &client_id),
        ("client_secret", &client_secret),
        ("scope", "offline"),
    ];

    let res = client
        .post(WHOOP_TOKEN_URL)
        .form(&params)
        .send()
        .await
        .map_err(|e| format!("Refresh request failed: {}", e))?;

    if !res.status().is_success() {
        let text = res.text().await.unwrap_or_default();
        return Err(format!("Refresh failed: {}", text));
    }

    let text = res.text().await.unwrap_or_default();
    let mut new_token: WhoopToken =
        serde_json::from_str(&text).map_err(|e| format!("Failed to parse refresh: {}", e))?;

    new_token.expires_at = Some(Utc::now().timestamp() as u64 + new_token.expires_in);
    save_token(new_token.clone());

    Ok(new_token)
}

pub async fn get_sleep_score() -> Result<SleepScore, String> {
    let token = refresh_token_if_needed().await?;

    let client = Client::new();

    // Get sleeps collection - defaults to newest first
    let res = client
        .get(&format!("{}/activity/sleep", WHOOP_API_BASE))
        .bearer_auth(&token.access_token)
        .query(&[("limit", "1")])
        .send()
        .await
        .map_err(|e| format!("Sleep request failed: {}", e))?;

    let status = res.status();
    let text = res.text().await.unwrap_or_default();

    if !status.is_success() {
        return Err(format!("Failed to get sleep data: {} - {}", status, text));
    }

    let json: serde_json::Value = serde_json::from_str(&text)
        .map_err(|e| format!("Failed to parse sleep response: {}", e))?;

    let record = json["records"][0]
        .as_object()
        .ok_or_else(|| "No sleep records found".to_string())?;

    let score = &record["score"];

    Ok(SleepScore {
        sleep_performance_percentage: score["sleep_performance_percentage"]
            .as_f64()
            .unwrap_or(0.0),
        sleep_consistency_percentage: score["sleep_consistency_percentage"]
            .as_f64()
            .unwrap_or(0.0),
        sleep_efficiency_percentage: score["sleep_efficiency_percentage"].as_f64().unwrap_or(0.0),
    })
}
