import { invoke } from '@tauri-apps/api/core';

export interface Habit {
  id: string;
  name: string;
  created_at: number;
}

export interface HabitEntry {
  habit_id: string;
  date: string;
  completed: boolean;
}

export interface HabitsResponse {
  habits: Habit[];
  entries: HabitEntry[];
}

export interface HabitMonthlySnapshot {
  year: number;
  month: number;
  days_in_month: number;
  days_completed: number;
  completion_rate: number;
}

export interface HabitHistoryResponse {
  habit_id: string;
  habit_name: string;
  snapshots: HabitMonthlySnapshot[];
}

export interface HabitMonthlySummary {
  habit_name: string;
  days_in_month: number;
  days_completed: number;
  completion_rate: number;
}

export interface MonthlySummary {
  year: number;
  month: number;
  habits: HabitMonthlySummary[];
}

export async function loadHabits(): Promise<HabitsResponse> {
  return invoke('load_habits');
}

export async function addHabit(name: string): Promise<HabitsResponse> {
  const id = Math.random().toString(36).substring(2, 11);
  return invoke('add_habit', { id, name });
}

export async function removeHabit(id: string): Promise<HabitsResponse> {
  return invoke('remove_habit', { id });
}

export async function toggleHabitEntry(habitId: string, date: string): Promise<HabitsResponse> {
  return invoke('toggle_habit_entry', { habitId, date });
}


export async function createHabitBackup(year: number, month: number): Promise<void> {
  return invoke('create_habit_backup', { year, month });
}

export async function getHabitHistory(habitId: string): Promise<HabitHistoryResponse> {
  return invoke('get_habit_history', { habitId });
}

export async function getMonthlySummary(year: number, month: number): Promise<MonthlySummary> {
  return invoke('get_monthly_summary', { year, month });
}
