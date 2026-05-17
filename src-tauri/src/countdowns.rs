use crate::db;
use crate::models::{Countdown, CountdownsResponse};
use chrono::Utc;

pub fn load_countdowns() -> Result<CountdownsResponse, String> {
    eprintln!("[countdowns] Loading countdowns from database");
    let mut response = db::load_countdowns_from_db()?;
    
    let now = Utc::now().timestamp();
    let original_len = response.countdowns.len();
    
    response.countdowns.retain(|c| c.target_timestamp > now);
    
    if response.countdowns.len() != original_len {
        eprintln!("[countdowns] Automatically removing {} expired countdown(s)", original_len - response.countdowns.len());
        save_countdowns(response.countdowns.clone())?;
    }
    
    Ok(response)
}

pub fn save_countdowns(countdowns: Vec<Countdown>) -> Result<(), String> {
    eprintln!("[countdowns] Saving {} countdowns to database", countdowns.len());
    db::save_countdowns_to_db(countdowns)
}

pub fn add_countdown(countdown: Countdown) -> Result<CountdownsResponse, String> {
    let mut current = load_countdowns()?.countdowns;
    current.push(countdown);
    save_countdowns(current)?;
    load_countdowns()
}

pub fn remove_countdown(id: String) -> Result<CountdownsResponse, String> {
    let mut current = load_countdowns()?.countdowns;
    current.retain(|c| c.id != id);
    save_countdowns(current)?;
    load_countdowns()
}
