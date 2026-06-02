const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { next: { revalidate: 30 } });
  if (!res.ok) throw new Error(`API error ${res.status} on ${path}`);
  return res.json();
}

export const api = {
  getLeagues: ()              => apiFetch<{ leagues: League[] }>("/leagues/"),
  getTodayMatches: ()         => apiFetch<{ matches: Match[] }>("/matches/today"),
  getLiveMatches: ()          => apiFetch<{ matches: Match[] }>("/matches/live"),
  getUpcomingMatches: ()      => apiFetch<{ matches: Match[] }>("/matches/upcoming"),
  getMatch: (id: number)      => apiFetch<Match>(`/matches/${id}`),
  getPrediction: (matchId: number) => apiFetch<Prediction>(`/predictions/match/${matchId}`),
  getHighConfidence: ()       => apiFetch<{ predictions: Prediction[] }>("/predictions/high-confidence"),
  getValueBets: ()            => apiFetch<{ predictions: Prediction[] }>("/predictions/value-bets"),
};

export type League = {
  id: number; name: string; country: string; type: string; season: string; slug: string;
};

export type Match = {
  id: number; home_team_id: number; away_team_id: number; league_id: number;
  kickoff_time: string; status: string; home_score: number | null; away_score: number | null;
};

export type Prediction = {
  id: number; match_id: number; mode: string;
  recommended_bet: string; expected_score: string | null;
  home_win_probability: number; draw_probability: number; away_win_probability: number;
  home_xg: number | null; away_xg: number | null;
  confidence_score: number; risk_level: string; value_rating: number;
  explanation: string; data_freshness_status: string; lineups_confirmed: boolean;
  generated_at: string;
};
