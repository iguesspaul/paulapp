use crate::models::{Habit, HabitEntry, HabitsResponse};
use crate::db;

pub async fn load_habits() -> Result<HabitsResponse, String> {
    eprintln!("[habits] Loading habits from database");
    db::load_habits_from_db()
}

pub async fn save_habits(habits: Vec<Habit>, entries: Vec<HabitEntry>) -> Result<(), String> {
    eprintln!("[habits] Saving habits to database");
    db::save_habits_to_db(habits, entries)
}

pub async fn add_habit(habit: Habit) -> Result<HabitsResponse, String> {
    let mut response = load_habits().await?;
    response.habits.push(habit);
    save_habits(response.habits.clone(), response.entries.clone()).await?;
    Ok(response)
}

pub async fn remove_habit(id: String) -> Result<HabitsResponse, String> {
    let mut response = load_habits().await?;
    response.habits.retain(|habit| habit.id != id);
    response.entries.retain(|entry| entry.habit_id != id);
    save_habits(response.habits.clone(), response.entries.clone()).await?;
    Ok(response)
}

pub async fn rename_habit(id: String, new_name: String) -> Result<HabitsResponse, String> {
    let mut response = load_habits().await?;
    if let Some(habit) = response.habits.iter_mut().find(|h| h.id == id) {
        habit.name = new_name;
    }
    save_habits(response.habits.clone(), response.entries.clone()).await?;
    Ok(response)
}

pub async fn toggle_entry(habit_id: String, date: String) -> Result<HabitsResponse, String> {
    let mut response = load_habits().await?;

    if let Some(entry) = response
        .entries
        .iter_mut()
        .find(|e| e.habit_id == habit_id && e.date == date)
    {
        entry.completed = !entry.completed;
    } else {
        response.entries.push(HabitEntry {
            habit_id: habit_id,
            date,
            completed: true,
        });
    }

    save_habits(response.habits.clone(), response.entries.clone()).await?;
    Ok(response)
}
