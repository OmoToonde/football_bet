import { api, type Match } from "@/lib/api";
import MatchCard from "@/components/match/MatchCard";
import PageHeader from "@/components/ui/PageHeader";

export const revalidate = 60;

interface Props { params: Promise<{ slug: string }> }

function groupByDay(matches: Match[]): Record<string, Match[]> {
  const groups: Record<string, Match[]> = {};
  for (const m of matches) {
    const d = new Date(m.kickoff_time);
    const today = new Date();
    const tomorrow = new Date(today); tomorrow.setDate(today.getDate() + 1);

    let key: string;
    if (d.toDateString() === today.toDateString()) key = "Today";
    else if (d.toDateString() === tomorrow.toDateString()) key = "Tomorrow";
    else key = d.toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "short" });

    groups[key] = groups[key] ?? [];
    groups[key].push(m);
  }
  return groups;
}

export default async function LeaguePage({ params }: Props) {
  const { slug } = await params;

  const data = await api.getLeagueMatches(slug).catch(() => null);
  if (!data) {
    return (
      <div className="px-4 py-8 text-center text-[#94A3B8]">
        <p>Could not load matches. Make sure the backend is running.</p>
      </div>
    );
  }

  const { league, matches } = data;
  const grouped = groupByDay(matches);
  const dayKeys = Object.keys(grouped);

  return (
    <div className="flex flex-col min-h-full">
      <PageHeader
        title={league.name}
        subtitle={`${league.country} · ${league.season}`}
        backHref="/"
        backLabel="All Competitions"
      />

      <div className="flex-1 px-4 py-4 space-y-6">
        {dayKeys.length === 0 ? (
          <div className="text-center py-12 text-[#94A3B8]">
            <p className="text-4xl mb-3">⚽</p>
            <p className="font-medium">No matches in the next 2 weeks</p>
            <p className="text-sm mt-1">Check back when the new season starts</p>
          </div>
        ) : (
          dayKeys.map((day) => (
            <section key={day}>
              <h2 className="text-xs font-semibold text-[#94A3B8] uppercase tracking-widest mb-2 px-1">
                {day}
              </h2>
              <div className="space-y-2">
                {grouped[day].map((m) => (
                  <MatchCard key={m.id} match={m} />
                ))}
              </div>
            </section>
          ))
        )}
      </div>

      <footer className="px-4 py-3 text-center text-[10px] text-[#94A3B8] border-t border-[#1E293B]">
        Predictions are not guaranteed. Bet responsibly. 18+
      </footer>
    </div>
  );
}
