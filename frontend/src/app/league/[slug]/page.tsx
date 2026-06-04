import { api, type Match } from "@/lib/api";
import MatchRow from "@/components/match/MatchRow";
import PageHeader from "@/components/ui/PageHeader";

export const revalidate = 60;

interface Props { params: Promise<{ slug: string }> }

function dedupe(matches: Match[]): Match[] {
  const seen = new Set<string>();
  const out: Match[] = [];
  for (const m of matches) {
    const key = `${m.kickoff_time.slice(0, 10)}-${(m.home_team ?? "").slice(0, 4).toLowerCase()}-${(m.away_team ?? "").slice(0, 4).toLowerCase()}`;
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(m);
  }
  return out;
}

function groupByDay(matches: Match[]): { label: string; matches: Match[] }[] {
  const groups: Record<string, Match[]> = {};
  const today = new Date();
  const tomorrow = new Date(today); tomorrow.setDate(today.getDate() + 1);

  for (const m of matches) {
    const d = new Date(m.kickoff_time);
    let key: string;
    if (d.toDateString() === today.toDateString()) key = "Today";
    else if (d.toDateString() === tomorrow.toDateString()) key = "Tomorrow";
    else key = d.toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "short" });
    groups[key] = groups[key] ?? [];
    groups[key].push(m);
  }
  return Object.entries(groups).map(([label, matches]) => ({ label, matches }));
}

export default async function LeaguePage({ params }: Props) {
  const { slug } = await params;

  const data = await api.getLeagueMatches(slug).catch(() => null);
  if (!data) {
    return <div className="px-4 py-8 text-center text-[#94A3B8]">Could not load matches. Make sure the backend is running.</div>;
  }

  const { league, matches } = data;
  const days = groupByDay(dedupe(matches));

  return (
    <div className="flex flex-col min-h-full">
      <PageHeader title={league.name} subtitle={`${league.country} · ${league.season}`} backHref="/" backLabel="All Competitions" />

      <div className="flex-1 px-3 py-3 space-y-3">
        {days.length === 0 ? (
          <div className="text-center py-12 text-[#94A3B8]">
            <p className="text-4xl mb-3">⚽</p>
            <p className="font-medium">No recent or upcoming matches</p>
            <p className="text-sm mt-1">Check back when the new season starts</p>
          </div>
        ) : (
          days.map((day) => (
            <div key={day.label} className="bg-[#111827] border border-[#1E293B] rounded-xl overflow-hidden">
              <div className="px-3 py-2 bg-[#0F172A] border-b border-[#1E293B]">
                <h2 className="text-[11px] font-bold text-[#94A3B8] uppercase tracking-widest">{day.label}</h2>
              </div>
              <div className="divide-y divide-[#1E293B]">
                {day.matches.map((m) => <MatchRow key={m.id} match={m} />)}
              </div>
            </div>
          ))
        )}
      </div>

      <footer className="px-4 py-3 text-center text-[10px] text-[#94A3B8] border-t border-[#1E293B]">
        Predictions are not guaranteed. Bet responsibly. 18+
      </footer>
    </div>
  );
}
