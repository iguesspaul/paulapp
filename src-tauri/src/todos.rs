use crate::models::{Todo, TodosResponse};
use crate::db;

pub async fn load_todos() -> Result<TodosResponse, String> {
    eprintln!("[todos] Loading todos from database");
    db::load_todos_from_db()
}

pub async fn save_todos(todos: Vec<Todo>) -> Result<(), String> {
    eprintln!("[todos] Saving todos to database");
    db::save_todos_to_db(todos)
}

pub async fn add_todo(todo: Todo) -> Result<TodosResponse, String> {
    let mut response = load_todos().await?;
    response.todos.push(todo);
    save_todos(response.todos.clone()).await?;
    Ok(response)
}

pub async fn remove_todo(id: String) -> Result<TodosResponse, String> {
    let mut response = load_todos().await?;
    response.todos.retain(|todo| todo.id != id);
    save_todos(response.todos.clone()).await?;
    Ok(response)
}
