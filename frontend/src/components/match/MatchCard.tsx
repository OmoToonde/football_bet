import Link from "next/link";
import { type Match, formatKickoff, riskColor } from "@/lib/api";
import FreshnessBadge from "@/components/ui/FreshnessBadge";

interface Props { match: Match; }

export default function MatchCard({ match: m }: Props) {
  const pred = m.prediction_summary;
  const slug = m.league_slug ?? "unknown";
  const href = `/league/${slug}/${m.id}`;

  return (
    <Link href={href}>
      <div className="bg-[#111827] border border-[#1E293B] rounded-xl p-4 hover:border-[#22C55E]/50 transition-colors">
        {/* Teams + score */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex-1">
            <p className="font-semibold text-[#F8FAFC] text-sm">{m.home_team}</p>
            <p className="text-[#94A3B8] text-xs mt-0.5">{m.away_team}</p>
          </div>
          {m.status === "live" ? (
            <div className="text-center px-3">
              <p className="text-lg font-bold text-[#F8FAFC]">
                {m.home_score ?? 0} – {m.away_score ?? 0}
              </p>
              <span className="text-[10px] text-[#EF4444] font-medium animate-pulse">LIVE</span>
            </div>
          ) : m.status === "finished" ? (
            <div className="text-center px-3">
              <p className="text-lg font-bold text-[#94A3B8]">
                {m.home_score ?? "–"} – {m.away_score ?? "–"}
              </p>
              <span className="text-[10px] text-[#94A3B8]">FT</span>
            </div>
          ) : (
            <div className="text-right">
              <p className="text-sm font-medium text-[#38BDF8]">{formatKickoff(m.kickoff_time)}</p>
            </div>
          )}
        </div>

        {/* Prediction summary */}
        {pred ? (
          <div className="flex items-center justify-between mt-2 pt-2 border-t border-[#1E293B]">
            <div className="flex items-center gap-2 flex-1 min-w-0">
              <span className="text-[#22C55E] text-xs font-medium truncate">{pred.recommended_bet}</span>
            </div>
            <div className="flex items-center gap-3 shrink-0 ml-2">
              {pred.expected_score && (
                <span className="text-[10px] text-[#94A3B8]">
                  Exp: <span className="text-[#38BDF8]">{pred.expected_score}</span>
                </span>
              )}
              <span className="text-[10px] text-[#94A3B8]">
                <span className="text-[#F8FAFC] font-medium">{pred.confidence_score?.toFixed(0)}%</span>
              </span>
              <span className={`text-[10px] font-medium ${riskColor(pred.risk_level)}`}>
                {pred.risk_level === "Live High Risk" ? "Live" : pred.risk_level}
              </span>
            </div>
          </div>
        ) : (
          <p className="text-[#94A3B8] text-xs mt-2 pt-2 border-t border-[#1E293B]">
            No prediction yet
          </p>
        )}
      </div>
    </Link>
  );
}
