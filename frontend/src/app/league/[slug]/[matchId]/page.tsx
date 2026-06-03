import { api } from "@/lib/api";
import RiskBadge from "@/components/ui/RiskBadge";
import FreshnessBadge from "@/components/ui/FreshnessBadge";
import CircularConfidence from "@/components/ui/CircularConfidence";
import MatchHero from "@/components/match/MatchHero";
import ProbabilityBar from "@/components/prediction/ProbabilityBar";
import ScorelineProbabilities from "@/components/prediction/ScorelineProbabilities";
import ExplanationCard from "@/components/prediction/ExplanationCard";
import Link from "next/link";

export const revalidate = 30;

interface Props { params: Promise<{ slug: string; matchId: string }> }

export default async function MatchDetailPage({ params }: Props) {
  const { slug, matchId } = await params;
  const id = Number(matchId);

  const [match, pred] = await Promise.allSettled([
    api.getMatch(id),
    api.getPrediction(id),
  ]);

  const m = match.status === "fulfilled" ? match.value : null;
  const p = pred.status === "fulfilled" ? pred.value : null;

  if (!m) {
    return <div className="px-4 py-8 text-center text-[#94A3B8]">Match not found.</div>;
  }

  const noBet = !p || p.recommended_bet === "No Bet Recommended";

  return (
    <div className="flex flex-col min-h-full">
      {/* Back link */}
      <div className="px-4 pt-4">
        <Link href={`/league/${slug}`} className="inline-flex items-center gap-1 text-[#94A3B8] text-sm hover:text-[#F8FAFC] transition-colors">
          <span>←</span>
          <span>{m.league_name ?? "League"}</span>
        </Link>
      </div>

      <div className="flex-1 px-4 py-4 space-y-3">
        {/* Match hero */}
        <MatchHero
          homeTeam={m.home_team ?? "Home"}
          awayTeam={m.away_team ?? "Away"}
          status={m.status}
          homeScore={m.home_score}
          awayScore={m.away_score}
          kickoff={m.kickoff_time}
          leagueName={m.league_name}
        />

        {p ? (
          <>
            {/* Hero recommendation card with circular confidence */}
            <div className={`relative overflow-hidden bg-[#111827] border rounded-2xl p-4 ${
              noBet ? "border-[#1E293B]" : "border-[#22C55E]/30 glow-green"
            }`}>
              <div className="flex items-center justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <p className="text-[10px] text-[#94A3B8] uppercase tracking-widest">Recommended Bet</p>
                  <p className={`text-xl font-black mt-1 leading-tight ${noBet ? "text-[#EF4444]" : "gradient-text"}`}>
                    {p.recommended_bet}
                  </p>
                  <div className="mt-2">
                    <RiskBadge level={p.risk_level} />
                  </div>
                </div>
                <CircularConfidence value={p.confidence_score ?? 0} size={76} />
              </div>

              {/* Metric row */}
              <div className="grid grid-cols-3 gap-2 mt-4">
                <div className="flex flex-col items-center bg-[#0F172A] rounded-xl py-2.5">
                  <span className="text-[10px] text-[#94A3B8] uppercase tracking-wide">Exp. Score</span>
                  <span className="text-base font-black text-[#38BDF8] mt-0.5">{p.expected_score ?? "—"}</span>
                </div>
                <div className="flex flex-col items-center bg-[#0F172A] rounded-xl py-2.5">
                  <span className="text-[10px] text-[#94A3B8] uppercase tracking-wide">Value</span>
                  <span className="text-base font-black text-[#F59E0B] mt-0.5">
                    {p.value_rating != null ? `${p.value_rating.toFixed(1)}` : "—"}
                    <span className="text-[10px] text-[#94A3B8] font-normal">/10</span>
                  </span>
                </div>
                <div className="flex flex-col items-center bg-[#0F172A] rounded-xl py-2.5">
                  <span className="text-[10px] text-[#94A3B8] uppercase tracking-wide">Confidence</span>
                  <span className="text-base font-black text-[#22C55E] mt-0.5">{p.confidence_score?.toFixed(0)}%</span>
                </div>
              </div>

              <div className="mt-3">
                <FreshnessBadge status={p.data_freshness_status} updatedAt={p.generated_at} />
              </div>
            </div>

            {/* Probability bar */}
            {!noBet && (
              <div className="bg-[#111827] border border-[#1E293B] rounded-2xl p-4">
                <p className="text-[10px] text-[#94A3B8] uppercase tracking-widest mb-3">Match Outcome</p>
                <ProbabilityBar
                  homeTeam={m.home_team ?? "Home"}
                  awayTeam={m.away_team ?? "Away"}
                  homeProb={p.home_win_probability}
                  drawProb={p.draw_probability}
                  awayProb={p.away_win_probability}
                />
              </div>
            )}

            {/* xG comparison */}
            {p.home_xg != null && p.away_xg != null && (
              <div className="bg-[#111827] border border-[#1E293B] rounded-2xl p-4">
                <p className="text-[10px] text-[#94A3B8] uppercase tracking-widest mb-3">Expected Goals (xG)</p>
                {(() => {
                  const total = (p.home_xg ?? 0) + (p.away_xg ?? 0);
                  const homePct = total > 0 ? ((p.home_xg ?? 0) / total) * 100 : 50;
                  return (
                    <>
                      <div className="flex items-end justify-between mb-2">
                        <div className="text-center">
                          <p className="text-3xl font-black text-[#22C55E] leading-none">{p.home_xg.toFixed(2)}</p>
                          <p className="text-[10px] text-[#94A3B8] mt-1 max-w-[100px] truncate">{m.home_team}</p>
                        </div>
                        <div className="text-center">
                          <p className="text-3xl font-black text-[#38BDF8] leading-none">{p.away_xg.toFixed(2)}</p>
                          <p className="text-[10px] text-[#94A3B8] mt-1 max-w-[100px] truncate">{m.away_team}</p>
                        </div>
                      </div>
                      <div className="flex h-2 rounded-full overflow-hidden gap-0.5">
                        <div className="bg-[#22C55E] rounded-l-full" style={{ width: `${homePct}%` }} />
                        <div className="bg-[#38BDF8] rounded-r-full" style={{ width: `${100 - homePct}%` }} />
                      </div>
                    </>
                  );
                })()}
              </div>
            )}

            {/* Scoreline probabilities */}
            {p.scoreline_probabilities && p.scoreline_probabilities.length > 0 && (
              <div className="bg-[#111827] border border-[#1E293B] rounded-2xl p-4">
                <ScorelineProbabilities
                  scorelines={p.scoreline_probabilities}
                  homeTeam={m.home_team ?? "Home"}
                  awayTeam={m.away_team ?? "Away"}
                />
              </div>
            )}

            {/* AI Explanation */}
            {p.explanation && (
              <ExplanationCard explanation={p.explanation} explanationJson={p.explanation_json} />
            )}
          </>
        ) : (
          <div className="bg-[#111827] border border-[#1E293B] rounded-2xl p-8 text-center">
            <p className="text-3xl mb-2">🔮</p>
            <p className="text-[#F8FAFC] text-sm font-medium">No prediction available yet</p>
            <p className="text-[#94A3B8] text-xs mt-1">Predictions are generated for upcoming fixtures.</p>
          </div>
        )}
      </div>

      <footer className="px-4 py-3 text-center text-[10px] text-[#94A3B8] border-t border-[#1E293B]">
        Predictions are not guaranteed. Bet responsibly. 18+
      </footer>
    </div>
  );
}
