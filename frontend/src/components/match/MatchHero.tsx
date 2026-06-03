import { formatKickoff } from "@/lib/api";

interface Props {
  homeTeam: string;
  awayTeam: string;
  status: string;
  homeScore: number | null;
  awayScore: number | null;
  kickoff: string;
  leagueName: string | null;
}

function teamInitials(name: string): string {
  const words = name.split(" ").filter(Boolean);
  if (words.length === 1) return words[0].slice(0, 3).toUpperCase();
  return (words[0][0] + words[words.length - 1][0]).toUpperCase();
}

export default function MatchHero({ homeTeam, awayTeam, status, homeScore, awayScore, kickoff, leagueName }: Props) {
  const isLive = status === "live";
  const isFinished = status === "finished";

  return (
    <div className="relative overflow-hidden bg-gradient-to-b from-[#111827] to-[#0F172A] border border-[#1E293B] rounded-2xl p-5">
      {/* Glow accents */}
      <div className="absolute -top-16 -left-10 w-40 h-40 rounded-full opacity-15 blur-3xl pointer-events-none"
        style={{ background: "radial-gradient(circle, #22C55E 0%, transparent 70%)" }} />
      <div className="absolute -bottom-16 -right-10 w-40 h-40 rounded-full opacity-10 blur-3xl pointer-events-none"
        style={{ background: "radial-gradient(circle, #38BDF8 0%, transparent 70%)" }} />

      <div className="relative">
        {/* Status pill */}
        <div className="flex justify-center mb-4">
          {isLive ? (
            <span className="flex items-center gap-1.5 text-[10px] font-bold text-[#EF4444] bg-[#EF4444]/10 border border-[#EF4444]/30 rounded-full px-3 py-1">
              <span className="w-1.5 h-1.5 rounded-full bg-[#EF4444] animate-pulse" />
              LIVE NOW
            </span>
          ) : isFinished ? (
            <span className="text-[10px] font-bold text-[#94A3B8] bg-[#0F172A] border border-[#1E293B] rounded-full px-3 py-1">
              FULL TIME
            </span>
          ) : (
            <span className="text-[10px] font-bold text-[#38BDF8] bg-[#38BDF8]/10 border border-[#38BDF8]/30 rounded-full px-3 py-1">
              {formatKickoff(kickoff).toUpperCase()}
            </span>
          )}
        </div>

        {/* Teams */}
        <div className="flex items-center justify-between gap-3">
          {/* Home */}
          <div className="flex-1 flex flex-col items-center text-center">
            <div className="w-14 h-14 rounded-2xl bg-[#0F172A] border border-[#1E293B] flex items-center justify-center mb-2">
              <span className="text-lg font-black text-[#F8FAFC]">{teamInitials(homeTeam)}</span>
            </div>
            <p className="text-xs font-semibold text-[#F8FAFC] leading-tight">{homeTeam}</p>
          </div>

          {/* Score / VS */}
          <div className="flex flex-col items-center px-2">
            {isFinished || isLive ? (
              <p className="text-3xl font-black text-[#F8FAFC] tabular-nums">
                {homeScore ?? 0}<span className="text-[#475569] mx-1">–</span>{awayScore ?? 0}
              </p>
            ) : (
              <p className="text-2xl font-black text-[#475569]">VS</p>
            )}
          </div>

          {/* Away */}
          <div className="flex-1 flex flex-col items-center text-center">
            <div className="w-14 h-14 rounded-2xl bg-[#0F172A] border border-[#1E293B] flex items-center justify-center mb-2">
              <span className="text-lg font-black text-[#F8FAFC]">{teamInitials(awayTeam)}</span>
            </div>
            <p className="text-xs font-semibold text-[#F8FAFC] leading-tight">{awayTeam}</p>
          </div>
        </div>

        {leagueName && (
          <p className="text-center text-[10px] text-[#94A3B8] mt-4">{leagueName}</p>
        )}
      </div>
    </div>
  );
}
