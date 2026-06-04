import { formatKickoff } from "@/lib/api";
import TeamBadge from "@/components/ui/TeamBadge";

interface Props {
  homeTeam: string;
  awayTeam: string;
  status: string;
  homeScore: number | null;
  awayScore: number | null;
  kickoff: string;
  leagueName: string | null;
}

export default function MatchHero({ homeTeam, awayTeam, status, homeScore, awayScore, kickoff, leagueName }: Props) {
  const isLive = status === "live";
  const isFinished = status === "finished";
  const played = isLive || isFinished;

  return (
    <div className="bg-[#111827] border border-[#1E293B] rounded-2xl px-4 pt-4 pb-5">
      {/* Competition + status */}
      <div className="flex items-center justify-center gap-2 mb-5">
        {leagueName && <span className="text-[11px] text-[#94A3B8] font-medium">{leagueName}</span>}
        {isLive && (
          <span className="flex items-center gap-1 text-[10px] font-bold text-[#22C55E]">
            <span className="w-1.5 h-1.5 rounded-full bg-[#22C55E] animate-pulse" />LIVE
          </span>
        )}
      </div>

      {/* Teams + score */}
      <div className="flex items-start justify-between gap-2">
        {/* Home */}
        <div className="flex-1 flex flex-col items-center text-center gap-2">
          <TeamBadge name={homeTeam} size={52} />
          <p className="text-sm font-semibold text-[#F8FAFC] leading-tight">{homeTeam}</p>
        </div>

        {/* Center */}
        <div className="flex flex-col items-center justify-center pt-3 px-1 min-w-[80px]">
          {played ? (
            <p className="text-4xl font-black text-[#F8FAFC] tabular-nums whitespace-nowrap">
              {homeScore ?? 0}<span className="text-[#475569] mx-1.5">-</span>{awayScore ?? 0}
            </p>
          ) : (
            <p className="text-2xl font-black text-[#475569]">VS</p>
          )}
          <span className="text-[10px] text-[#94A3B8] mt-1.5">
            {isFinished ? "Full Time" : isLive ? "In play" : formatKickoff(kickoff)}
          </span>
        </div>

        {/* Away */}
        <div className="flex-1 flex flex-col items-center text-center gap-2">
          <TeamBadge name={awayTeam} size={52} />
          <p className="text-sm font-semibold text-[#F8FAFC] leading-tight">{awayTeam}</p>
        </div>
      </div>
    </div>
  );
}
