import { invoke } from '@tauri-apps/api/core';

export interface Todo {
  id: string;
  name: string;
  status: 1 | 2 | 3; // 1: not started, 2: in progress, 3: completed
  urgency: 1 | 2 | 3;
  created_at: number;
}

export interface TodosResponse {
  todos: Todo[];
}

export async function loadTodos(): Promise<TodosResponse> {
  return invoke('load_todos');
}

export async function addTodo(name: string, urgency: 1 | 2 | 3, status: 1 | 2 | 3): Promise<TodosResponse> {
  const id = Math.random().toString(36).substring(2, 11);
  return invoke('add_todo', { id, name, urgency, status });
}

export async function removeTodo(id: string): Promise<TodosResponse> {
  return invoke('remove_todo', { id });
}

export async function updateStatus(id: string, status: 1 | 2 | 3): Promise<TodosResponse> {
  return invoke('update_todo_status', { id, status });
}
