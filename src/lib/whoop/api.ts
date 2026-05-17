import { invoke } from '@tauri-apps/api/core';

export interface SleepScore {
  sleepPerformancePercentage: number;
  sleepConsistencyPercentage: number;
  sleepEfficiencyPercentage: number;
}

export async function getWhoopAuthUrl(): Promise<string> {
  return await invoke('get_whoop_auth_url');
}

export async function exchangeWhoopToken(code: string): Promise<void> {
  await invoke('exchange_whoop_token', { code });
}

export async function getWhoopSleepScore(): Promise<SleepScore> {
  return await invoke('get_whoop_sleep_score');
}
