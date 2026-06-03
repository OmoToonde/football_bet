import Link from "next/link";
import { type League } from "@/lib/api";

const LEAGUE_FLAGS: Record<string, string> = {
  "premier-league":   "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
  "la-liga":          "🇪🇸",
  "serie-a":          "🇮🇹",
  "bundesliga":       "🇩🇪",
  "ligue-1":          "🇫🇷",
  "eredivisie":       "🇳🇱",
  "champions-league": "🏆",
};

// Accent gradient per league for the left stripe
const LEAGUE_ACCENT: Record<string, string> = {
  "premier-league":   "linear-gradient(180deg, #3D195B, #963CBD)",
  "la-liga":          "linear-gradient(180deg, #EE8707, #FF4B44)",
  "serie-a":          "linear-gradient(180deg, #0468B1, #00A0E6)",
  "bundesliga":       "linear-gradient(180deg, #D20515, #FF2D37)",
  "ligue-1":          "linear-gradient(180deg, #091C3E, #DA0B52)",
  "eredivisie":       "linear-gradient(180deg, #FF6200, #FF9E1B)",
  "champions-league": "linear-gradient(180deg, #0A1A4F, #1D4ED8)",
};

export default function LeagueCard({ league }: { league: League }) {
  const flag = LEAGUE_FLAGS[league.slug] ?? "⚽";
  const accent = LEAGUE_ACCENT[league.slug] ?? "linear-gradient(180deg, #22C55E, #16A34A)";
  const hasLive = (league.live_now ?? 0) > 0;
  const isUCL = league.slug === "champions-league";

  return (
    <Link href={`/league/${league.slug}`}>
      <div className={`relative overflow-hidden bg-[#111827] border border-[#1E293B] rounded-2xl card-hover ${isUCL ? "glow-gold" : ""}`}>
        {/* Accent stripe */}
        <div className="absolute left-0 top-0 bottom-0 w-1" style={{ background: accent }} />

        <div className="pl-4 pr-4 py-3.5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#0F172A] border border-[#1E293B] flex items-center justify-center text-xl shrink-0">
              {flag}
            </div>
            <div>
              <h3 className={`font-bold text-sm ${isUCL ? "gradient-text-gold" : "text-[#F8FAFC]"}`}>
                {league.name}
              </h3>
              <p className="text-[11px] text-[#94A3B8]">{league.country} · {league.season}</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="text-right">
              {hasLive ? (
                <span className="text-[10px] font-bold text-[#EF4444] flex items-center gap-1 justify-end">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#EF4444] animate-pulse" />
                  {league.live_now} LIVE
                </span>
              ) : (league.upcoming_matches ?? 0) > 0 ? (
                <span className="text-[10px] text-[#94A3B8] font-medium">
                  {league.upcoming_matches} upcoming
                </span>
              ) : (
                <span className="text-[10px] text-[#94A3B8]/50">off-season</span>
              )}
              {league.best_pick && league.best_pick !== "No Bet Recommended" && (
                <p className="text-[11px] text-[#22C55E] font-medium mt-0.5 max-w-[140px] truncate">
                  {league.best_pick}
                </p>
              )}
            </div>
            <span className="text-[#475569] text-xl">›</span>
          </div>
        </div>
      </div>
    </Link>
  );
}
