use crate::models::{Countdown, CountdownsResponse, Habit, HabitEntry, HabitsResponse, Todo, TodosResponse};
use chrono::Datelike;
use once_cell::sync::Lazy;
use rusqlite::{params, Connection};
use std::path::PathBuf;
use std::sync::Mutex;

static DB_CONNECTION: Lazy<Mutex<Option<Connection>>> = Lazy::new(|| Mutex::new(None));

fn get_db_path() -> Result<PathBuf, String> {
    dirs::config_dir()
        .ok_or_else(|| "Could not determine config directory".to_string())
        .map(|dir| dir.join("paulapp").join("paulapp.db"))
}

pub fn init_db() -> Result<(), String> {
    let db_path = get_db_path()?;

    if let Some(parent) = db_path.parent() {
        std::fs::create_dir_all(parent)
            .map_err(|e| format!("Failed to create config directory: {}", e))?;
    }

    let conn = Connection::open(&db_path).map_err(|e| format!("Failed to open database: {}", e))?;

    eprintln!("[db] Initializing at: {}", db_path.display());

    // Create tables if they don't exist
    conn.execute_batch(
        "
        CREATE TABLE IF NOT EXISTS habits (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_at INTEGER NOT NULL
        );
        
        CREATE TABLE IF NOT EXISTS habit_entries (
            habit_id TEXT NOT NULL,
            date TEXT NOT NULL,
            completed BOOLEAN NOT NULL,
            PRIMARY KEY (habit_id, date),
            FOREIGN KEY(habit_id) REFERENCES habits(id)
        );
        
        CREATE TABLE IF NOT EXISTS todos (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            urgency INTEGER NOT NULL,
            status INTEGER NOT NULL,
            created_at INTEGER NOT NULL
        );
        
        CREATE TABLE IF NOT EXISTS habit_monthly_snapshots (
            id TEXT PRIMARY KEY,
            habit_id TEXT NOT NULL,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            habit_name TEXT NOT NULL,
            days_in_month INTEGER NOT NULL,
            days_completed INTEGER NOT NULL,
            completion_rate REAL NOT NULL,
            created_at INTEGER NOT NULL,
            UNIQUE(habit_id, year, month),
            FOREIGN KEY(habit_id) REFERENCES habits(id)
        );
        
        CREATE TABLE IF NOT EXISTS countdowns (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            target_timestamp INTEGER NOT NULL,
            created_at INTEGER NOT NULL
        );
        ",
    )
    .map_err(|e| format!("Failed to create tables: {}", e))?;

    // Migration: Add status column to todos if it doesn't exist
    let _ = conn.execute(
        "ALTER TABLE todos ADD COLUMN status INTEGER NOT NULL DEFAULT 0",
        [],
    );

    *DB_CONNECTION.lock().unwrap() = Some(conn);
    eprintln!("[db] Database initialized successfully");
    Ok(())
}

fn get_connection() -> Result<Connection, String> {
    let db_path = get_db_path()?;
    Connection::open(&db_path).map_err(|e| format!("Failed to open database connection: {}", e))
}

// Helper: Load all todos from database
pub fn load_todos_from_db() -> Result<TodosResponse, String> {
    let conn = get_connection()?;
    let mut stmt = conn
        .prepare("SELECT id, name, urgency, status, created_at FROM todos ORDER BY created_at DESC")
        .map_err(|e| format!("Failed to prepare query: {}", e))?;

    let todos = stmt
        .query_map([], |row| {
            Ok(Todo {
                id: row.get(0)?,
                name: row.get(1)?,
                urgency: row.get(2)?,
                status: row.get(3)?,
                created_at: row.get(4)?,
            })
        })
        .map_err(|e| format!("Failed to query todos: {}", e))?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| format!("Failed to collect todos: {}", e))?;

    Ok(TodosResponse { todos })
}

// Helper: Save todos to database
pub fn save_todos_to_db(todos: Vec<Todo>) -> Result<(), String> {
    let conn = get_connection()?;

    // Clear existing todos
    conn.execute("DELETE FROM todos", [])
        .map_err(|e| format!("Failed to clear todos: {}", e))?;

    // Insert all todos
    for todo in todos {
        conn.execute(
            "INSERT INTO todos (id, name, urgency, status, created_at) VALUES (?, ?, ?, ?, ?)",
            params![
                &todo.id,
                &todo.name,
                &todo.urgency,
                &todo.status,
                &todo.created_at
            ],
        )
        .map_err(|e| format!("Failed to insert todo: {}", e))?;
    }

    Ok(())
}

pub fn update_todo_status(id: &str, status: u8) -> Result<TodosResponse, String> {
    let conn = get_connection()?;

    conn.execute(
        "UPDATE todos SET status = ? WHERE id = ?",
        params![status, id],
    )
    .map_err(|e| format!("Failed to update todo status: {}", e))?;

    load_todos_from_db()
}

// Helper: Load all countdowns from database
pub fn load_countdowns_from_db() -> Result<CountdownsResponse, String> {
    let conn = get_connection()?;
    let mut stmt = conn
        .prepare("SELECT id, name, target_timestamp, created_at FROM countdowns ORDER BY target_timestamp ASC")
        .map_err(|e| format!("Failed to prepare query: {}", e))?;

    let countdowns = stmt
        .query_map([], |row| {
            Ok(Countdown {
                id: row.get(0)?,
                name: row.get(1)?,
                target_timestamp: row.get(2)?,
                created_at: row.get(3)?,
            })
        })
        .map_err(|e| format!("Failed to query countdowns: {}", e))?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| format!("Failed to collect countdowns: {}", e))?;

    Ok(CountdownsResponse { countdowns })
}

// Helper: Save countdowns to database
pub fn save_countdowns_to_db(countdowns: Vec<Countdown>) -> Result<(), String> {
    let conn = get_connection()?;

    conn.execute("DELETE FROM countdowns", [])
        .map_err(|e| format!("Failed to clear countdowns: {}", e))?;

    for countdown in countdowns {
        conn.execute(
            "INSERT INTO countdowns (id, name, target_timestamp, created_at) VALUES (?, ?, ?, ?)",
            params![
                &countdown.id,
                &countdown.name,
                &countdown.target_timestamp,
                &countdown.created_at
            ],
        )
        .map_err(|e| format!("Failed to insert countdown: {}", e))?;
    }

    Ok(())
}

// Helper: Load all habits and entries from database
pub fn load_habits_from_db() -> Result<HabitsResponse, String> {
    let conn = get_connection()?;

    // Load habits
    let mut stmt = conn
        .prepare("SELECT id, name, created_at FROM habits ORDER BY rowid")
        .map_err(|e| format!("Failed to prepare habits query: {}", e))?;

    let habits = stmt
        .query_map([], |row| {
            Ok(Habit {
                id: row.get(0)?,
                name: row.get(1)?,
                created_at: row.get(2)?,
            })
        })
        .map_err(|e| format!("Failed to query habits: {}", e))?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| format!("Failed to collect habits: {}", e))?;

    // Load entries
    let mut stmt = conn
        .prepare("SELECT habit_id, date, completed FROM habit_entries")
        .map_err(|e| format!("Failed to prepare entries query: {}", e))?;

    let entries = stmt
        .query_map([], |row| {
            Ok(HabitEntry {
                habit_id: row.get(0)?,
                date: row.get(1)?,
                completed: row.get(2)?,
            })
        })
        .map_err(|e| format!("Failed to query entries: {}", e))?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| format!("Failed to collect entries: {}", e))?;

    Ok(HabitsResponse { habits, entries })
}

// Helper: Save habits and entries to database
pub fn save_habits_to_db(habits: Vec<Habit>, entries: Vec<HabitEntry>) -> Result<(), String> {
    let conn = get_connection()?;

    // Clear existing entries
    conn.execute("DELETE FROM habit_entries", [])
        .map_err(|e| format!("Failed to clear entries: {}", e))?;

    // Find habits to delete
    let mut stmt = conn
        .prepare("SELECT id FROM habits")
        .map_err(|e| format!("Failed to prepare habits query: {}", e))?;
    
    let current_ids: Vec<String> = stmt
        .query_map([], |row| row.get(0))
        .map_err(|e| format!("Failed to query habits: {}", e))?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| format!("Failed to collect habits: {}", e))?;

    // Delete snapshots and habits that are no longer in the list
    for id in current_ids {
        if !habits.iter().any(|h| h.id == id) {
            conn.execute("DELETE FROM habit_monthly_snapshots WHERE habit_id = ?", params![&id])
                .map_err(|e| format!("Failed to delete snapshots for removed habit: {}", e))?;
            conn.execute("DELETE FROM habits WHERE id = ?", params![&id])
                .map_err(|e| format!("Failed to delete removed habit: {}", e))?;
        }
    }

    // Upsert habits
    for habit in habits {
        conn.execute(
            "INSERT OR REPLACE INTO habits (id, name, created_at) VALUES (?, ?, ?)",
            params![&habit.id, &habit.name, &habit.created_at],
        )
        .map_err(|e| format!("Failed to insert habit: {}", e))?;
    }

    // Insert entries
    for entry in entries {
        conn.execute(
            "INSERT INTO habit_entries (habit_id, date, completed) VALUES (?, ?, ?)",
            params![&entry.habit_id, &entry.date, &entry.completed],
        )
        .map_err(|e| format!("Failed to insert entry: {}", e))?;
    }

    Ok(())
}

// Retrieve: Get habit name by ID
pub fn get_habit_name(habit_id: &str) -> Result<String, String> {
    let conn = get_connection()?;

    let mut stmt = conn
        .prepare("SELECT name FROM habits WHERE id = ?")
        .map_err(|e| format!("Failed to prepare query: {}", e))?;

    let name = stmt
        .query_row(params![habit_id], |row| row.get(0))
        .map_err(|_| "Habit not found".to_string())?;

    Ok(name)
}

// Backup: Create monthly snapshot of habit completion stats
pub fn create_monthly_snapshot(year: i32, month: i32) -> Result<(), String> {
    let conn = get_connection()?;

    // Get all habits
    let mut stmt = conn
        .prepare("SELECT id, name FROM habits")
        .map_err(|e| format!("Failed to prepare habits query: {}", e))?;

    let habits: Vec<(String, String)> = stmt
        .query_map([], |row| Ok((row.get(0)?, row.get(1)?)))
        .map_err(|e| format!("Failed to query habits: {}", e))?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| format!("Failed to collect habits: {}", e))?;

    // Determine days in month
    let days_in_month = if month == 12 {
        chrono::NaiveDate::from_ymd_opt(year + 1, 1, 1)
            .and_then(|d| d.pred_opt())
            .map(|d| d.day() as i32)
            .ok_or("Invalid date")?
    } else {
        chrono::NaiveDate::from_ymd_opt(year, month as u32 + 1, 1)
            .and_then(|d| d.pred_opt())
            .map(|d| d.day() as i32)
            .ok_or("Invalid date")?
    };

    // For each habit, count completions in the month
    for (habit_id, habit_name) in habits {
        let month_str = format!("{:04}-{:02}", year, month);

        let mut stmt = conn.prepare(
            "SELECT COUNT(*) FROM habit_entries WHERE habit_id = ? AND date LIKE ? AND completed = 1"
        ).map_err(|e| format!("Failed to prepare count query: {}", e))?;

        let days_completed: i32 = stmt
            .query_row(params![&habit_id, format!("{}%", month_str)], |row| {
                row.get(0)
            })
            .map_err(|e| format!("Failed to count completions: {}", e))?;

        let completion_rate = if days_in_month > 0 {
            days_completed as f64 / days_in_month as f64
        } else {
            0.0
        };

        let snapshot_id = format!("{}-{}-{:04}{:02}", habit_id, "snapshot", year, month);
        let now = chrono::Utc::now().timestamp();

        // Insert or replace snapshot
        conn.execute(
            "INSERT OR REPLACE INTO habit_monthly_snapshots (id, habit_id, year, month, habit_name, days_in_month, days_completed, completion_rate, created_at) 
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            params![&snapshot_id, &habit_id, year, month, &habit_name, days_in_month, days_completed, completion_rate, now],
        ).map_err(|e| format!("Failed to insert snapshot: {}", e))?;
    }

    eprintln!("[db] Created monthly snapshot for {}-{:02}", year, month);
    Ok(())
}

// Retrieve: Get historical snapshots for a specific habit
pub fn get_habit_history(habit_id: &str) -> Result<Vec<(i32, i32, i32, i32, f64)>, String> {
    let conn = get_connection()?;

    let mut stmt = conn
        .prepare(
            "SELECT year, month, days_in_month, days_completed, completion_rate 
         FROM habit_monthly_snapshots 
         WHERE habit_id = ? 
         ORDER BY year ASC, month ASC",
        )
        .map_err(|e| format!("Failed to prepare history query: {}", e))?;

    let history = stmt
        .query_map(params![habit_id], |row| {
            Ok((
                row.get(0)?, // year
                row.get(1)?, // month
                row.get(2)?, // days_in_month
                row.get(3)?, // days_completed
                row.get(4)?, // completion_rate
            ))
        })
        .map_err(|e| format!("Failed to query history: {}", e))?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| format!("Failed to collect history: {}", e))?;

    Ok(history)
}

// Retrieve: Get all snapshots (aggregated across all habits for a given month)
pub fn get_monthly_summary(year: i32, month: i32) -> Result<Vec<(String, i32, i32, f64)>, String> {
    let conn = get_connection()?;

    let mut stmt = conn
        .prepare(
            "SELECT habit_name, days_in_month, days_completed, completion_rate 
         FROM habit_monthly_snapshots 
         WHERE year = ? AND month = ? 
         ORDER BY habit_name ASC",
        )
        .map_err(|e| format!("Failed to prepare summary query: {}", e))?;

    let summary = stmt
        .query_map(params![year, month], |row| {
            Ok((
                row.get(0)?, // habit_name
                row.get(1)?, // days_in_month
                row.get(2)?, // days_completed
                row.get(3)?, // completion_rate
            ))
        })
        .map_err(|e| format!("Failed to query summary: {}", e))?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| format!("Failed to collect summary: {}", e))?;

    Ok(summary)
}
