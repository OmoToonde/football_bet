import Link from "next/link";
import { type League } from "@/lib/api";

interface Props {
  league: League;
}

export default function LeagueCard({ league }: Props) {
  return (
    <Link href={`/league/${league.slug}`}>
      <div className="bg-[#111827] border border-[#1E293B] rounded-xl p-4 hover:border-[#22C55E] transition-colors cursor-pointer">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-[#F8FAFC]">{league.name}</h3>
            <p className="text-sm text-[#94A3B8]">{league.country} · {league.season}</p>
          </div>
          <span className="text-[#22C55E] text-xl">›</span>
        </div>
      </div>
    </Link>
  );
}
