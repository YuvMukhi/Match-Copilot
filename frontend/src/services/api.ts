import type {
  ChatApiResponse,
  ChatRequestPayload,
  MatchState,
  MatchSummary,
  TeamDetail,
  TeamSummary,
} from '../types';

const BASE_URL = '/api/v1';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorMsg = `HTTP Error ${res.status}`;
    try {
      const errorJson = await res.json();
      if (errorJson?.error?.message) {
        errorMsg = errorJson.error.message;
      }
    } catch {
      // Ignore JSON parse error on non-json error responses
    }
    throw new Error(errorMsg);
  }
  return res.json() as Promise<T>;
}

export const api = {
  async getMatches(): Promise<MatchSummary[]> {
    const res = await fetch(`${BASE_URL}/matches`);
    return handleResponse<MatchSummary[]>(res);
  },

  async getMatchState(matchId: string, over: number, teamId: string): Promise<MatchState> {
    const res = await fetch(`${BASE_URL}/matches/${matchId}/state?over=${over}&team_id=${teamId}`);
    return handleResponse<MatchState>(res);
  },

  async getTeams(): Promise<TeamSummary[]> {
    const res = await fetch(`${BASE_URL}/teams`);
    return handleResponse<TeamSummary[]>(res);
  },

  async getTeamDetail(teamId: string, over: number): Promise<TeamDetail> {
    const res = await fetch(`${BASE_URL}/teams/${teamId}?over=${over}`);
    return handleResponse<TeamDetail>(res);
  },

  async sendChat(payload: ChatRequestPayload): Promise<ChatApiResponse> {
    const res = await fetch(`${BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
    return handleResponse<ChatApiResponse>(res);
  },
};
