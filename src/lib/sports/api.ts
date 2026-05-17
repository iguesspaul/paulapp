import { invoke } from '@tauri-apps/api/core';

export interface TeamStanding {
  position: number;
  team_id: number;
  team_name: string;
  short_name: string;
  played: number;
  won: number;
  drawn: number;
  lost: number;
  goals_for: number;
  goals_against: number;
  goal_difference: number;
  points: number;
}

export interface StandingsResponse {
  league_id: string;
  season_id: number;
  standings: TeamStanding[];
  cached_at: number;
}

export interface UpcomingMatch {
  event_id: number;
  slug: string;
  round: number;
  start_timestamp: number;
  status: string;
  home_team_id: number;
  home_team_name: string;
  away_team_id: number;
  away_team_name: string;
}

export interface UpcomingMatchesResponse {
  league_id: string;
  season_id: number;
  matches: UpcomingMatch[];
}

export async function getStandings(leagueId: string): Promise<StandingsResponse> {
  return invoke('get_standings',  {leagueId} );
}

export async function getUpcomingMatches(leagueId: string): Promise<UpcomingMatchesResponse> {
  return invoke('get_upcoming_matches', { leagueId });
}