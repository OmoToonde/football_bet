import { type Prediction } from "@/lib/api";
import FreshnessBadge from "@/components/ui/FreshnessBadge";
import RiskBadge from "@/components/ui/RiskBadge";

interface Props {
  prediction: Prediction;
  homeTeam: string;
  awayTeam: string;
}

export default function PredictionCard({ prediction: p, homeTeam, awayTeam }: Props) {
  const noBet = p.recommended_bet === "No Bet Recommended";

  return (
    <div className="bg-[#111827] border border-[#1E293B] rounded-xl p-5 space-y-4">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-[#94A3B8] uppercase tracking-wide">Recommended Bet</p>
          <p className={`text-lg font-bold mt-0.5 ${noBet ? "text-[#EF4444]" : "text-[#22C55E]"}`}>
            {p.recommended_bet}
          </p>
        </div>
        <RiskBadge level={p.risk_level} />
      </div>

      {/* Score + probabilities */}
      {!noBet && (
        <div className="grid grid-cols-3 gap-2 text-center">
          <div className="bg-[#0F172A] rounded-lg p-2">
            <p className="text-xs text-[#94A3B8]">{homeTeam}</p>
            <p className="text-lg font-bold text-[#F8FAFC]">
              {((p.home_win_probability ?? 0) * 100).toFixed(0)}%
            </p>
          </div>
          <div className="bg-[#0F172A] rounded-lg p-2">
            <p className="text-xs text-[#94A3B8]">Draw</p>
            <p className="text-lg font-bold text-[#F8FAFC]">
              {((p.draw_probability ?? 0) * 100).toFixed(0)}%
            </p>
          </div>
          <div className="bg-[#0F172A] rounded-lg p-2">
            <p className="text-xs text-[#94A3B8]">{awayTeam}</p>
            <p className="text-lg font-bold text-[#F8FAFC]">
              {((p.away_win_probability ?? 0) * 100).toFixed(0)}%
            </p>
          </div>
        </div>
      )}

      {/* Expected score */}
      {p.expected_score && (
        <div className="flex justify-between items-center text-sm">
          <span className="text-[#94A3B8]">Expected Score</span>
          <span className="font-semibold text-[#38BDF8]">
            {homeTeam} {p.expected_score} {awayTeam}
          </span>
        </div>
      )}

      {/* Confidence + value */}
      <div className="flex gap-4 text-sm">
        <div>
          <span className="text-[#94A3B8]">Confidence </span>
          <span className="font-semibold text-[#F8FAFC]">{p.confidence_score?.toFixed(0)}%</span>
        </div>
        {p.value_rating != null && (
          <div>
            <span className="text-[#94A3B8]">Value </span>
            <span className="font-semibold text-[#F59E0B]">{p.value_rating.toFixed(1)}/10</span>
          </div>
        )}
      </div>

      {/* Explanation */}
      {p.explanation && (
        <div className="text-xs text-[#94A3B8] border-t border-[#1E293B] pt-3 leading-relaxed">
          {p.explanation}
        </div>
      )}

      {/* Freshness */}
      <FreshnessBadge status={p.data_freshness_status} updatedAt={p.generated_at} />
    </div>
  );
}
