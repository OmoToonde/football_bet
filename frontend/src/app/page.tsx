import { api, type Match } from "@/lib/api";
import LeagueGroup from "@/components/match/LeagueGroup";
import QuickAccessBar from "@/components/ui/QuickAccessBar";
import DateStrip from "@/components/ui/DateStrip";

export const revalidate = 60;

// League display order
const LEAGUE_ORDER = [
  "premier-league", "la-liga", "serie-a", "bundesliga",
  "ligue-1", "eredivisie", "champions-league",
];

function groupByLeague(matches: Match[]) {
  const groups: Record<string, { slug: string; name: string; matches: Match[] }> = {};
  for (const m of matches) {
    const slug = m.league_slug ?? "unknown";
    if (!groups[slug]) {
      groups[slug] = { slug, name: m.league_name ?? "Unknown", matches: [] };
    }
    groups[slug].matches.push(m);
  }
  return Object.values(groups).sort(
    (a, b) => LEAGUE_ORDER.indexOf(a.slug) - LEAGUE_ORDER.indexOf(b.slug)
  );
}

export default async function HomePage() {
  const { matches } = await api.getRecentMatches().catch(() => ({ matches: [] }));
  const grouped = groupByLeague(matches);

  return (
    <main className="min-h-screen text-[#F8FAFC]">
      {/* Compact top bar */}
      <header className="flex items-center justify-between px-4 py-3 border-b border-[#1E293B] bg-[#0B1220] sticky top-0 z-10">
        <div className="flex items-center gap-2">
          <span className="text-xl">⚽</span>
          <h1 className="text-base font-black tracking-tight gradient-text">Football Intelligence</h1>
        </div>
        <span className="text-[10px] text-[#475569]">18+</span>
      </header>

      <DateStrip />
      <QuickAccessBar />

      <section className="px-3 py-3 space-y-3">
        {grouped.length === 0 ? (
          <div className="text-center py-16 text-[#94A3B8]">
            <p className="text-4xl mb-3">⚽</p>
            <p className="font-medium text-[#F8FAFC]">No matches to show</p>
            <p className="text-sm mt-1">Start the backend and populate match data</p>
          </div>
        ) : (
          grouped.map((g) => (
            <LeagueGroup key={g.slug} slug={g.slug} name={g.name} matches={g.matches} />
          ))
        )}
      </section>

      <footer className="px-4 py-5 border-t border-[#1E293B] text-[10px] text-[#94A3B8] text-center">
        Predictions are not guaranteed. Bet responsibly. 18+
      </footer>
    </main>
  );
}
