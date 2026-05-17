// src-tauri/src/models.rs
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct TeamStanding {
    pub position: u32,
    pub team_id: u32,
    pub team_name: String,
    pub short_name: String,
    pub played: u32,
    pub won: u32,
    pub drawn: u32,
    pub lost: u32,
    pub goals_for: u32,
    pub goals_against: u32,
    pub goal_difference: i32,
    pub points: u32,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct StandingsResponse {
    pub league_id: String,
    pub season_id: u32,
    pub standings: Vec<TeamStanding>,
    pub cached_at: i64,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct UpcomingMatch {
    pub event_id: u64,
    pub slug: String,
    pub round: u32,
    pub start_timestamp: u64,
    pub status: String,
    pub home_team_id: u32,
    pub home_team_name: String,
    pub away_team_id: u32,
    pub away_team_name: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct UpcomingMatchesResponse {
    pub league_id: String,
    pub season_id: u32,
    pub matches: Vec<UpcomingMatch>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Todo {
    pub id: String,
    pub name: String,
    pub status: u8,
    pub urgency: u8,
    pub created_at: i64,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct TodosResponse {
    pub todos: Vec<Todo>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Habit {
    pub id: String,
    pub name: String,
    pub created_at: i64,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct HabitEntry {
    pub habit_id: String,
    pub date: String,
    pub completed: bool,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct HabitsResponse {
    pub habits: Vec<Habit>,
    pub entries: Vec<HabitEntry>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct HabitMonthlySnapshot {
    pub year: i32,
    pub month: i32,
    pub days_in_month: i32,
    pub days_completed: i32,
    pub completion_rate: f64,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct HabitHistoryResponse {
    pub habit_id: String,
    pub habit_name: String,
    pub snapshots: Vec<HabitMonthlySnapshot>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct MonthlySummary {
    pub year: i32,
    pub month: i32,
    pub habits: Vec<HabitMonthlySummary>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct HabitMonthlySummary {
    pub habit_name: String,
    pub days_in_month: i32,
    pub days_completed: i32,
    pub completion_rate: f64,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct OllamaGenerateRequest {
    pub model: String,
    pub prompt: String,
    pub stream: bool,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct OllamaGenerateResponse {
    pub response: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct WhoopToken {
    pub access_token: String,
    pub refresh_token: String,
    pub expires_in: u64,
    pub expires_at: Option<u64>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct SleepScore {
    pub sleep_performance_percentage: f64,
    pub sleep_consistency_percentage: f64,
    pub sleep_efficiency_percentage: f64,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Countdown {
    pub id: String,
    pub name: String,
    pub target_timestamp: i64,
    pub created_at: i64,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct CountdownsResponse {
    pub countdowns: Vec<Countdown>,
}
#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct UVIndexResponse {
    pub max_uv_index: f64,
    pub max_uv_time: String,
}
