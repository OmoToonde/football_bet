import { api } from "@/lib/api";
import PageHeader from "@/components/ui/PageHeader";
import RiskBadge from "@/components/ui/RiskBadge";
import FreshnessBadge from "@/components/ui/FreshnessBadge";
import ProbabilityBar from "@/components/prediction/ProbabilityBar";
import ScorelineProbabilities from "@/components/prediction/ScorelineProbabilities";
import ExplanationCard from "@/components/prediction/ExplanationCard";
import { formatKickoff } from "@/lib/api";

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
    return (
      <div className="px-4 py-8 text-center text-[#94A3B8]">
        Match not found.
      </div>
    );
  }

  const noBet = !p || p.recommended_bet === "No Bet Recommended";

  return (
    <div className="flex flex-col min-h-full">
      <PageHeader
        title={`${m.home_team} vs ${m.away_team}`}
        subtitle={`${m.league_name} · ${formatKickoff(m.kickoff_time)}`}
        backHref={`/league/${slug}`}
        backLabel={m.league_name ?? "League"}
      />

      <div className="flex-1 px-4 py-4 space-y-4">
        {/* Score / Status banner */}
        {m.status === "finished" && (
          <div className="bg-[#111827] border border-[#1E293B] rounded-xl p-4 text-center">
            <p className="text-3xl font-black text-[#F8FAFC]">
              {m.home_score} – {m.away_score}
            </p>
            <p className="text-xs text-[#94A3B8] mt-1">Full Time</p>
          </div>
        )}
        {m.status === "live" && (
          <div className="bg-[#111827] border border-[#EF4444]/30 rounded-xl p-4 text-center">
            <p className="text-3xl font-black text-[#F8FAFC]">
              {m.home_score} – {m.away_score}
            </p>
            <p className="text-xs text-[#EF4444] font-semibold animate-pulse mt-1">● LIVE</p>
          </div>
        )}

        {/* Prediction card */}
        {p ? (
          <>
            {/* Recommendation */}
            <div className="bg-[#111827] border border-[#1E293B] rounded-xl p-4 space-y-3">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-[10px] text-[#94A3B8] uppercase tracking-wide">Recommended Bet</p>
                  <p className={`text-xl font-bold mt-0.5 ${noBet ? "text-[#EF4444]" : "text-[#22C55E]"}`}>
                    {p.recommended_bet}
                  </p>
                </div>
                <RiskBadge level={p.risk_level} />
              </div>

              {/* Confidence + Value */}
              <div className="flex gap-4 text-sm">
                <div>
                  <span className="text-[#94A3B8]">Confidence </span>
                  <span className="font-bold text-[#F8FAFC]">{p.confidence_score?.toFixed(0)}%</span>
                </div>
                {p.value_rating != null && (
                  <div>
                    <span className="text-[#94A3B8]">Value </span>
                    <span className="font-bold text-[#F59E0B]">{p.value_rating?.toFixed(1)}/10</span>
                  </div>
                )}
                {p.expected_score && (
                  <div>
                    <span className="text-[#94A3B8]">Score </span>
                    <span className="font-bold text-[#38BDF8]">{p.expected_score}</span>
                  </div>
                )}
              </div>

              <FreshnessBadge status={p.data_freshness_status} updatedAt={p.generated_at} />
            </div>

            {/* Probability bar */}
            {!noBet && (
              <div className="bg-[#111827] border border-[#1E293B] rounded-xl p-4">
                <ProbabilityBar
                  homeTeam={m.home_team ?? "Home"}
                  awayTeam={m.away_team ?? "Away"}
                  homeProb={p.home_win_probability}
                  drawProb={p.draw_probability}
                  awayProb={p.away_win_probability}
                />
              </div>
            )}

            {/* xG */}
            {p.home_xg != null && p.away_xg != null && (
              <div className="bg-[#111827] border border-[#1E293B] rounded-xl p-4">
                <p className="text-[10px] text-[#94A3B8] uppercase tracking-wide mb-3">Expected Goals (xG)</p>
                <div className="grid grid-cols-3 text-center gap-2">
                  <div>
                    <p className="text-xs text-[#94A3B8] truncate">{m.home_team}</p>
                    <p className="text-2xl font-black text-[#22C55E]">{p.home_xg.toFixed(2)}</p>
                  </div>
                  <div className="flex items-center justify-center">
                    <span className="text-[#94A3B8] text-lg">vs</span>
                  </div>
                  <div>
                    <p className="text-xs text-[#94A3B8] truncate">{m.away_team}</p>
                    <p className="text-2xl font-black text-[#38BDF8]">{p.away_xg.toFixed(2)}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Scoreline probabilities */}
            {p.scoreline_probabilities && p.scoreline_probabilities.length > 0 && (
              <div className="bg-[#111827] border border-[#1E293B] rounded-xl p-4">
                <ScorelineProbabilities
                  scorelines={p.scoreline_probabilities}
                  homeTeam={m.home_team ?? "Home"}
                  awayTeam={m.away_team ?? "Away"}
                />
              </div>
            )}

            {/* AI Explanation */}
            {p.explanation && (
              <ExplanationCard
                explanation={p.explanation}
                explanationJson={p.explanation_json}
              />
            )}
          </>
        ) : (
          <div className="bg-[#111827] border border-[#1E293B] rounded-xl p-6 text-center">
            <p className="text-[#94A3B8] text-sm">No prediction available for this match yet.</p>
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
