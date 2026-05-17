use reqwest::Client;
use serde_json::Value;
use crate::models::UVIndexResponse;

pub async fn get_max_uv_index() -> Result<UVIndexResponse, String> {
    let client = Client::new();
    let api_key = "AIzaSyB-pvFXc7ZSRM0Q0aCIkpGxlFRXnYF2Rz8";
    let lat = "18.033237";
    let lon = "-76.763064";

    // URLs for 24h history and 24h forecast
    let history_url = format!("https://weather.googleapis.com/v1/history/hours:lookup?key={}&location.latitude={}&location.longitude={}&hours=24", api_key, lat, lon);
    let forecast_url = format!("https://weather.googleapis.com/v1/forecast/hours:lookup?key={}&location.latitude={}&location.longitude={}&hours=24", api_key, lat, lon);

    let history_req = client.get(history_url).send();
    let forecast_req = client.get(forecast_url).send();

    let (history_res, forecast_res) = tokio::join!(history_req, forecast_req);

    let mut history_hours: Vec<Value> = Vec::new();
    let mut forecast_hours: Vec<Value> = Vec::new();

    if let Ok(res) = history_res {
        if res.status().is_success() {
            if let Ok(json) = res.json::<Value>().await {
                if let Some(hours) = json["historyHours"].as_array() {
                    history_hours.extend(hours.clone());
                }
            }
        }
    }

    if let Ok(res) = forecast_res {
        if res.status().is_success() {
            if let Ok(json) = res.json::<Value>().await {
                if let Some(hours) = json["forecastHours"].as_array() {
                    forecast_hours.extend(hours.clone());
                }
            }
        }
    }

    if history_hours.is_empty() && forecast_hours.is_empty() {
        return Err("No weather data found".to_string());
    }

    // Determine "Today" based on the first hour of forecast (or last of history)
    // This represents the current date at the target location.
    let today_ref = forecast_hours.first().or(history_hours.last());
    let (t_year, t_month, t_day) = if let Some(hour) = today_ref {
        let dt = &hour["displayDateTime"];
        (
            dt["year"].as_i64().unwrap_or(0),
            dt["month"].as_i64().unwrap_or(0),
            dt["day"].as_i64().unwrap_or(0),
        )
    } else {
        (0, 0, 0)
    };

    let mut max_uv: f64 = -1.0;
    let mut max_time = String::new();

    // Loop through combined data but ONLY for today's date
    for hour in history_hours.iter().chain(forecast_hours.iter()) {
        let dt = &hour["displayDateTime"];
        let h_year = dt["year"].as_i64().unwrap_or(0);
        let h_month = dt["month"].as_i64().unwrap_or(0);
        let h_day = dt["day"].as_i64().unwrap_or(0);

        if h_year == t_year && h_month == t_month && h_day == t_day {
            if let Some(uv) = hour["uvIndex"].as_f64() {
                if uv > max_uv {
                    max_uv = uv;
                    let h = dt["hours"].as_u64().unwrap_or(0);
                    let m = dt["minutes"].as_u64().unwrap_or(0);
                    max_time = format!("{:02}:{:02}", h, m);
                }
            }
        }
    }

    // If no UV data for today found (maybe early morning calls), just take the global max of next 24h
    if max_uv < 0.0 {
        for hour in forecast_hours.iter() {
            if let Some(uv) = hour["uvIndex"].as_f64() {
                if uv > max_uv {
                    max_uv = uv;
                    let dt = &hour["displayDateTime"];
                    let h = dt["hours"].as_u64().unwrap_or(0);
                    let m = dt["minutes"].as_u64().unwrap_or(0);
                    max_time = format!("{:02}:{:02}", h, m);
                }
            }
        }
    }

    if max_uv < 0.0 {
        return Err("No UV index data found".to_string());
    }

    Ok(UVIndexResponse {
        max_uv_index: max_uv,
        max_uv_time: max_time,
    })
}
