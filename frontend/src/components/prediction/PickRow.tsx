import Link from "next/link";
import { type Prediction } from "@/lib/api";
import TeamBadge from "@/components/ui/TeamBadge";
import RiskBadge from "@/components/ui/RiskBadge";

interface Props {
  pred: Prediction;
  metric?: "confidence" | "value";
}

export default function PickRow({ pred: p, metric = "confidence" }: Props) {
  const slug = p.league_slug ?? "unknown";
  const href = `/league/${slug}/${p.match_id}`;
  const hasTeams = p.home_team && p.away_team;

  const metricNode = metric === "value" ? (
    <div className="flex flex-col items-center shrink-0">
      <span className={`text-lg font-black ${
        (p.value_rating ?? 0) >= 8 ? "text-[#22C55E]" :
        (p.value_rating ?? 0) >= 6 ? "text-[#F59E0B]" : "text-[#94A3B8]"
      }`}>{p.value_rating?.toFixed(1)}</span>
      <span className="text-[9px] text-[#94A3B8]">/10 value</span>
    </div>
  ) : (
    <div className="flex flex-col items-center shrink-0">
      <span className="text-lg font-black text-[#22C55E]">{p.confidence_score?.toFixed(0)}%</span>
      <span className="text-[9px] text-[#94A3B8]">confidence</span>
    </div>
  );

  return (
    <Link href={href}>
      <div className="flex items-center gap-3 px-3 py-3 hover:bg-[#1A2232] transition-colors">
        <div className="flex-1 min-w-0">
          {hasTeams && (
            <div className="flex items-center gap-2 mb-1.5">
              <TeamBadge name={p.home_team!} logo={p.home_logo} size={18} />
              <span className="text-xs text-[#CBD5E1] truncate">{p.home_team}</span>
              <span className="text-[10px] text-[#475569]">v</span>
              <TeamBadge name={p.away_team!} logo={p.away_logo} size={18} />
              <span className="text-xs text-[#CBD5E1] truncate">{p.away_team}</span>
            </div>
          )}
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-[#22C55E] truncate">{p.recommended_bet}</span>
            <RiskBadge level={p.risk_level} />
          </div>
          {p.expected_score && (
            <p className="text-[10px] text-[#94A3B8] mt-0.5">Expected score {p.expected_score}</p>
          )}
        </div>
        {metricNode}
      </div>
    </Link>
  );
}
