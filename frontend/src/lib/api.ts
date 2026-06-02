const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string, revalidate = 30): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { next: { revalidate } });
  if (!res.ok) throw new Error(`API ${res.status} — ${path}`);
  return res.json();
}

export const api = {
  getLeagues:          ()                => apiFetch<{ leagues: League[] }>("/leagues/"),
  getLeagueBySlug:     (slug: string)    => apiFetch<League>(`/leagues/slug/${slug}`),
  getLeagueMatches:    (slug: string)    => apiFetch<{ league: League; matches: Match[] }>(`/leagues/slug/${slug}/matches`),
  getTodayMatches:     ()                => apiFetch<{ matches: Match[] }>("/matches/today", 60),
  getLiveMatches:      ()                => apiFetch<{ matches: Match[] }>("/matches/live", 10),
  getUpcomingMatches:  ()                => apiFetch<{ matches: Match[] }>("/matches/upcoming"),
  getMatch:            (id: number)      => apiFetch<Match>(`/matches/${id}`),
  getPrediction:       (matchId: number) => apiFetch<Prediction>(`/predictions/match/${matchId}`),
  getHighConfidence:   ()                => apiFetch<{ predictions: Prediction[] }>("/predictions/high-confidence"),
  getValueBets:        ()                => apiFetch<{ predictions: Prediction[] }>("/predictions/value-bets"),
};

export type League = {
  id: number;
  name: string;
  country: string;
  type: string;
  season: string;
  slug: string;
  upcoming_matches?: number;
  live_now?: number;
  next_kickoff?: string | null;
  best_pick?: string | null;
  highest_confidence?: number | null;
};

export type PredictionSummary = {
  recommended_bet: string;
  expected_score: string | null;
  confidence_score: number;
  risk_level: string;
  value_rating: number;
  data_freshness_status: string;
};

export type Match = {
  id: number;
  home_team_id: number;
  home_team: string | null;
  away_team_id: number;
  away_team: string | null;
  league_id: number;
  league_name: string | null;
  league_slug: string | null;
  kickoff_time: string;
  venue: string | null;
  status: string;
  home_score: number | null;
  away_score: number | null;
  prediction_summary: PredictionSummary | null;
};

export type ScorelineProbability = {
  home_goals: number;
  away_goals: number;
  probability: number;
};

export type Prediction = {
  id: number;
  match_id: number;
  mode: string;
  recommended_bet: string;
  expected_score: string | null;
  home_win_probability: number;
  draw_probability: number;
  away_win_probability: number;
  home_xg: number | null;
  away_xg: number | null;
  confidence_score: number;
  risk_level: string;
  value_rating: number;
  explanation: string;
  data_freshness_status: string;
  lineups_confirmed: boolean;
  generated_at: string;
  scoreline_probabilities?: ScorelineProbability[];
};

export function formatKickoff(iso: string): string {
  const d = new Date(iso);
  const today = new Date();
  const tomorrow = new Date(today);
  tomorrow.setDate(today.getDate() + 1);

  const time = d.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
  if (d.toDateString() === today.toDateString()) return `Today ${time}`;
  if (d.toDateString() === tomorrow.toDateString()) return `Tomorrow ${time}`;
  return d.toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short" }) + ` ${time}`;
}

export function riskColor(level: string): string {
  switch (level) {
    case "Low":              return "text-[#22C55E]";
    case "Medium":           return "text-[#F59E0B]";
    case "High":             return "text-[#F97316]";
    case "Very High":        return "text-[#EF4444]";
    case "Live High Risk":   return "text-[#EF4444]";
    default:                 return "text-[#94A3B8]";
  }
}
