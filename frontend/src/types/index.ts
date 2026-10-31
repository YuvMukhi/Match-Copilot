export type Language = 'en' | 'hinglish';

export interface MatchSummary {
  id: string;
  name: string;
  short_name: string;
  team1: string;
  team2: string;
  venue: string;
  status: string;
  current_innings: number;
  total_overs: number;
}

export interface MatchDeliverySummary {
  over_number: number;
  ball_in_over: number;
  bowler_name: string;
  batter_name: string;
  runs_batter: number;
  runs_extras: number;
  extra_type?: string | null;
  is_wicket: boolean;
  dismissal_kind?: string | null;
  display_text: string;
}

export interface PlayerScoreBreakdownItem {
  player_id: string;
  player_name: string;
  role: string;
  is_captain: boolean;
  is_vice_captain: boolean;
  multiplier: number;
  total_points: number;
  runs: number;
  wickets: number;
  events: string[];
}

export interface MatchState {
  match_id: string;
  match_name: string;
  over: number;
  total_overs: number;
  runs: number;
  wickets: number;
  run_rate: number;
  current_batters: string[];
  current_bowler: string;
  recent_balls: MatchDeliverySummary[];
  team_points?: number | null;
  team_breakdown?: PlayerScoreBreakdownItem[] | null;
}

export interface PlayerInTeam {
  id: string;
  name: string;
  team: string;
  role: string;
  credits: number;
  is_captain: boolean;
  is_vice_captain: boolean;
  current_points?: number;
}

export interface TeamSummary {
  id: string;
  name: string;
  user_name: string;
  player_count: number;
}

export interface TeamDetail {
  id: string;
  name: string;
  user_name: string;
  captain_name: string;
  vice_captain_name: string;
  total_points: number;
  players: PlayerInTeam[];
}

export interface EvidencePayload {
  tool_called: string;
  title: string;
  summary: string;
  confidence_note?: string | null;
  table_headers: string[];
  table_rows: Record<string, string | number>[];
  raw_data?: Record<string, unknown> | null;
}

export interface ChatMessageItem {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  evidence?: EvidencePayload | null;
  over: number;
  timestamp: string;
  isOutOfScope?: boolean;
}

export interface ChatRequestPayload {
  match_id: string;
  team_id: string;
  over: number;
  message: string;
  language: string;
}

export interface ChatApiResponse {
  answer: string;
  evidence?: EvidencePayload | null;
  over: number;
  language: string;
  is_out_of_scope: boolean;
}
