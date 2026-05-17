import { invoke } from '@tauri-apps/api/core';

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

/**
 * Create a monthly backup/snapshot for a given year and month.
 * This captures the completion rate and statistics for all habits in that month.
 * Can be called manually or automatically at month-end.
 */
export async function createHabitBackup(year: number, month: number): Promise<void> {
  return invoke('create_habit_backup', { year, month });
}

/**
 * Get historical monthly snapshots for a specific habit.
 * Use this to build progress graphs and visualizations.
 * Returns all snapshots ordered chronologically.
 */
export async function getHabitHistory(habitId: string): Promise<HabitHistoryResponse> {
  return invoke('get_habit_history', { habitId });
}

/**
 * Get Summary of all habits for a specific month.
 * Use this to see overall progress for a given month.
 */
export async function getMonthlySummary(year: number, month: number): Promise<MonthlySummary> {
  return invoke('get_monthly_summary', { year, month });
}
