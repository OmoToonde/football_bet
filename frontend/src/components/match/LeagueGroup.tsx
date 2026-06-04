import Link from "next/link";
import { type Match } from "@/lib/api";
import MatchRow from "./MatchRow";

const LEAGUE_FLAGS: Record<string, string> = {
  "premier-league":   "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
  "la-liga":          "🇪🇸",
  "serie-a":          "🇮🇹",
  "bundesliga":       "🇩🇪",
  "ligue-1":          "🇫🇷",
  "eredivisie":       "🇳🇱",
  "champions-league": "🏆",
};

interface Props {
  slug: string;
  name: string;
  matches: Match[];
}

export default function LeagueGroup({ slug, name, matches }: Props) {
  const flag = LEAGUE_FLAGS[slug] ?? "⚽";

  return (
    <div className="bg-[#111827] border border-[#1E293B] rounded-xl overflow-hidden">
      {/* League header */}
      <Link href={`/league/${slug}`}>
        <div className="flex items-center justify-between px-3 py-2.5 bg-[#0F172A] hover:bg-[#141d2e] transition-colors border-b border-[#1E293B]">
          <div className="flex items-center gap-2">
            <span className="text-base leading-none">{flag}</span>
            <span className="text-xs font-bold text-[#F8FAFC] tracking-wide">{name}</span>
          </div>
          <span className="text-[#475569] text-base">›</span>
        </div>
      </Link>

      {/* Match rows */}
      <div className="divide-y divide-[#1E293B]">
        {matches.map((m) => <MatchRow key={m.id} match={m} />)}
      </div>
    </div>
  );
}
