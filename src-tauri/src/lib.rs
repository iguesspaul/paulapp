mod ai;
mod db;
mod habits;
mod models;
mod sports;
mod todos;
mod whoop;
mod weather;
mod countdowns;

#[tauri::command]
async fn get_news_summary() -> Result<String, String> {
    ai::generate_news_summary().await
}

#[tauri::command]
async fn get_standings(league_id: String) -> Result<models::StandingsResponse, String> {
    sports::fetch_standings(&league_id).await
}

#[tauri::command]
async fn get_upcoming_matches(
    league_id: String,
) -> Result<models::UpcomingMatchesResponse, String> {
    sports::fetch_upcoming_matches(&league_id).await
}

#[tauri::command]
async fn load_todos() -> Result<models::TodosResponse, String> {
    todos::load_todos().await
}

#[tauri::command]
async fn add_todo(id: String, name: String, urgency: u8, status: u8) -> Result<models::TodosResponse, String> {
    let todo = models::Todo {
        id,
        name,
        urgency,
        status,
        created_at: chrono::Utc::now().timestamp(),
    };
    todos::add_todo(todo).await
}

#[tauri::command]
async fn remove_todo(id: String) -> Result<models::TodosResponse, String> {
    todos::remove_todo(id).await
}

#[tauri::command]
async fn load_habits() -> Result<models::HabitsResponse, String> {
    habits::load_habits().await
}

#[tauri::command]
async fn add_habit(id: String, name: String) -> Result<models::HabitsResponse, String> {
    let habit = models::Habit {
        id,
        name,
        created_at: chrono::Utc::now().timestamp(),
    };
    habits::add_habit(habit).await
}

#[tauri::command]
async fn remove_habit(id: String) -> Result<models::HabitsResponse, String> {
    habits::remove_habit(id).await
}

#[tauri::command]
async fn rename_habit(id: String, new_name: String) -> Result<models::HabitsResponse, String> {
    habits::rename_habit(id, new_name).await
}

#[tauri::command]
async fn toggle_habit_entry(
    habit_id: String,
    date: String,
) -> Result<models::HabitsResponse, String> {
    habits::toggle_entry(habit_id, date).await
}

#[tauri::command]
fn create_habit_backup(year: i32, month: i32) -> Result<(), String> {
    db::create_monthly_snapshot(year, month)
}

#[tauri::command]
fn get_habit_history(habit_id: String) -> Result<models::HabitHistoryResponse, String> {
    // Get habit name from database
    let habit_name = db::get_habit_name(&habit_id)?;
    
    let history_data = db::get_habit_history(&habit_id)?;
    
    let snapshots = history_data.iter().map(|(y, m, days_in, completed, rate)| {
        models::HabitMonthlySnapshot {
            year: *y,
            month: *m,
            days_in_month: *days_in,
            days_completed: *completed,
            completion_rate: *rate,
        }
    }).collect();
    
    Ok(models::HabitHistoryResponse {
        habit_id,
        habit_name,
        snapshots,
    })
}

#[tauri::command]
fn get_monthly_summary(year: i32, month: i32) -> Result<models::MonthlySummary, String> {
    let summary_data = db::get_monthly_summary(year, month)?;
    
    let habits = summary_data.iter().map(|(name, days_in, completed, rate)| {
        models::HabitMonthlySummary {
            habit_name: name.clone(),
            days_in_month: *days_in,
            days_completed: *completed,
            completion_rate: *rate,
        }
    }).collect();
    
    Ok(models::MonthlySummary {
        year,
        month,
        habits,
    })
}

#[tauri::command]
fn update_todo_status(id: String, status: u8) -> Result<models::TodosResponse, String> {
    db::update_todo_status(&id, status)
}

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[tauri::command]
fn get_whoop_auth_url() -> Result<String, String> {
    whoop::get_auth_url()
}

#[tauri::command]
async fn exchange_whoop_token(code: String) -> Result<(), String> {
    whoop::exchange_token(code).await
}

#[tauri::command]
async fn get_uv_index() -> Result<crate::models::UVIndexResponse, String> {
    weather::get_max_uv_index().await
}

#[tauri::command]
async fn get_whoop_sleep_score() -> Result<crate::models::SleepScore, String> {
    whoop::get_sleep_score().await
}

#[tauri::command]
fn load_countdowns() -> Result<crate::models::CountdownsResponse, String> {
    countdowns::load_countdowns()
}

#[tauri::command]
fn add_countdown(id: String, name: String, target_timestamp: i64) -> Result<crate::models::CountdownsResponse, String> {
    let now = chrono::Utc::now().timestamp();
    let countdown = crate::models::Countdown {
        id,
        name,
        target_timestamp,
        created_at: now,
    };
    countdowns::add_countdown(countdown)
}

#[tauri::command]
fn remove_countdown(id: String) -> Result<crate::models::CountdownsResponse, String> {
    countdowns::remove_countdown(id)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    // Initialize database
    if let Err(e) = db::init_db() {
        eprintln!("[startup] Failed to initialize database: {}", e);
    }


    tauri::Builder::default()
        .plugin(tauri_plugin_sql::Builder::new().build())
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            greet,
            get_standings,
            get_upcoming_matches,
            load_todos,
            add_todo,
            remove_todo,
            update_todo_status,
            load_habits,
            add_habit,
            remove_habit,
            rename_habit,
            toggle_habit_entry,
            create_habit_backup,
            get_habit_history,
            get_monthly_summary,
            get_news_summary,
            get_whoop_auth_url,
            exchange_whoop_token,
            get_whoop_sleep_score,
            get_uv_index,
            load_countdowns,
            add_countdown,
            remove_countdown
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
