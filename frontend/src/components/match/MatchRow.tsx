import Link from "next/link";
import { type Match } from "@/lib/api";
import TeamBadge from "@/components/ui/TeamBadge";

function statusBlock(m: Match) {
  if (m.status === "live") {
    return (
      <div className="flex flex-col items-center justify-center w-12 shrink-0">
        <span className="text-[11px] font-bold text-[#22C55E]">LIVE</span>
        <span className="w-1.5 h-1.5 rounded-full bg-[#22C55E] animate-pulse mt-0.5" />
      </div>
    );
  }
  if (m.status === "finished") {
    return (
      <div className="flex items-center justify-center w-12 shrink-0">
        <span className="text-[11px] font-semibold text-[#94A3B8]">FT</span>
      </div>
    );
  }
  const t = new Date(m.kickoff_time).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
  return (
    <div className="flex items-center justify-center w-12 shrink-0">
      <span className="text-[11px] font-semibold text-[#94A3B8]">{t}</span>
    </div>
  );
}

export default function MatchRow({ match: m }: { match: Match }) {
  const slug = m.league_slug ?? "unknown";
  const href = `/league/${slug}/${m.id}`;
  const played = m.status === "finished" || m.status === "live";
  const homeWin = played && (m.home_score ?? 0) > (m.away_score ?? 0);
  const awayWin = played && (m.away_score ?? 0) > (m.home_score ?? 0);
  const pick = m.prediction_summary?.recommended_bet;

  return (
    <Link href={href}>
      <div className="flex items-center gap-2 px-3 py-2.5 hover:bg-[#1A2232] transition-colors">
        {statusBlock(m)}

        {/* Vertical divider */}
        <div className="w-px self-stretch bg-[#1E293B]" />

        {/* Teams */}
        <div className="flex-1 min-w-0 space-y-1.5">
          <div className="flex items-center gap-2">
            <TeamBadge name={m.home_team ?? "?"} logo={m.home_logo} size={22} />
            <span className={`text-sm truncate ${homeWin ? "font-bold text-[#F8FAFC]" : "text-[#CBD5E1]"}`}>
              {m.home_team}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <TeamBadge name={m.away_team ?? "?"} logo={m.away_logo} size={22} />
            <span className={`text-sm truncate ${awayWin ? "font-bold text-[#F8FAFC]" : "text-[#CBD5E1]"}`}>
              {m.away_team}
            </span>
          </div>
        </div>

        {/* Scores or pick chip */}
        {played ? (
          <div className="flex flex-col items-center w-6 shrink-0 space-y-1.5">
            <span className={`text-sm tabular-nums ${homeWin ? "font-bold text-[#F8FAFC]" : "text-[#94A3B8]"}`}>
              {m.home_score ?? 0}
            </span>
            <span className={`text-sm tabular-nums ${awayWin ? "font-bold text-[#F8FAFC]" : "text-[#94A3B8]"}`}>
              {m.away_score ?? 0}
            </span>
          </div>
        ) : pick && pick !== "No Bet Recommended" ? (
          <div className="flex items-center shrink-0 max-w-[88px]">
            <span className="text-[10px] font-medium text-[#22C55E] bg-[#22C55E]/10 border border-[#22C55E]/20 rounded px-1.5 py-0.5 truncate">
              {pick}
            </span>
          </div>
        ) : (
          <span className="text-[#475569] text-lg shrink-0">›</span>
        )}
      </div>
    </Link>
  );
}
