import Link from "next/link";
import { type League, formatKickoff, riskColor } from "@/lib/api";

const LEAGUE_FLAGS: Record<string, string> = {
  "premier-league":   "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
  "la-liga":          "🇪🇸",
  "serie-a":          "🇮🇹",
  "bundesliga":       "🇩🇪",
  "ligue-1":          "🇫🇷",
  "eredivisie":       "🇳🇱",
  "champions-league": "🏆",
};

export default function LeagueCard({ league }: { league: League }) {
  const flag = LEAGUE_FLAGS[league.slug] ?? "⚽";
  const hasLive = (league.live_now ?? 0) > 0;

  return (
    <Link href={`/league/${league.slug}`}>
      <div className="bg-[#111827] border border-[#1E293B] rounded-xl p-4 hover:border-[#22C55E]/50 active:scale-[0.99] transition-all cursor-pointer">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2.5">
            <span className="text-2xl leading-none">{flag}</span>
            <div>
              <h3 className="font-semibold text-[#F8FAFC] text-sm">{league.name}</h3>
              <p className="text-xs text-[#94A3B8]">{league.country} · {league.season}</p>
            </div>
          </div>
          <div className="text-right shrink-0 ml-2">
            {hasLive ? (
              <span className="text-[10px] font-semibold text-[#EF4444] flex items-center gap-1 justify-end">
                <span className="w-1.5 h-1.5 rounded-full bg-[#EF4444] animate-pulse" />
                {league.live_now} live
              </span>
            ) : (league.upcoming_matches ?? 0) > 0 ? (
              <span className="text-[10px] text-[#94A3B8]">{league.upcoming_matches} upcoming</span>
            ) : null}
            <span className="text-[#94A3B8] text-lg ml-1">›</span>
          </div>
        </div>

        {/* Best pick preview */}
        {league.best_pick && league.best_pick !== "No Bet Recommended" && (
          <div className="mt-3 pt-3 border-t border-[#1E293B] flex items-center justify-between">
            <p className="text-xs text-[#22C55E] font-medium truncate flex-1">{league.best_pick}</p>
            {league.highest_confidence != null && (
              <span className="text-xs text-[#94A3B8] ml-2 shrink-0">
                {league.highest_confidence.toFixed(0)}% conf
              </span>
            )}
          </div>
        )}
      </div>
    </Link>
  );
}
