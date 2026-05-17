import { invoke } from '@tauri-apps/api/core';

export interface Countdown {
  id: string;
  name: string;
  target_timestamp: number;
  created_at: number;
}

export interface CountdownsResponse {
  countdowns: Countdown[];
}

export async function loadCountdowns(): Promise<CountdownsResponse> {
  return invoke('load_countdowns');
}

export async function addCountdown(name: string, targetTimestamp: number): Promise<CountdownsResponse> {
  const id = Math.random().toString(36).substring(2, 11);
  return invoke('add_countdown', { id, name, targetTimestamp });
}

export async function removeCountdown(id: string): Promise<CountdownsResponse> {
  return invoke('remove_countdown', { id });
}
