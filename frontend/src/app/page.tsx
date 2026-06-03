import { api } from "@/lib/api";
import LeagueCard from "@/components/league/LeagueCard";
import QuickAccessBar from "@/components/ui/QuickAccessBar";

export const revalidate = 60;

export default async function HomePage() {
  const { leagues } = await api.getLeagues().catch(() => ({ leagues: [] }));

  const totalLive = leagues.reduce((n, l) => n + (l.live_now ?? 0), 0);
  const totalUpcoming = leagues.reduce((n, l) => n + (l.upcoming_matches ?? 0), 0);

  return (
    <main className="min-h-screen text-[#F8FAFC]">
      {/* Hero header with radial glow */}
      <header className="relative overflow-hidden px-5 pt-8 pb-6 border-b border-[#1E293B]">
        <div
          className="absolute -top-24 -right-16 w-64 h-64 rounded-full opacity-20 blur-3xl pointer-events-none"
          style={{ background: "radial-gradient(circle, #22C55E 0%, transparent 70%)" }}
        />
        <div
          className="absolute -bottom-32 -left-20 w-72 h-72 rounded-full opacity-10 blur-3xl pointer-events-none"
          style={{ background: "radial-gradient(circle, #38BDF8 0%, transparent 70%)" }}
        />
        <div className="relative">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-2xl">⚽</span>
            <h1 className="text-2xl font-black tracking-tight gradient-text">
              Football Intelligence
            </h1>
          </div>
          <p className="text-sm text-[#94A3B8]">
            AI-powered betting insights · Real-time analysis
          </p>

          {/* Live stat row */}
          <div className="flex gap-2 mt-4">
            <div className="flex items-center gap-1.5 bg-[#0F172A]/80 border border-[#1E293B] rounded-full px-3 py-1.5">
              <span className="w-2 h-2 rounded-full bg-[#EF4444] animate-pulse" />
              <span className="text-xs font-semibold text-[#F8FAFC]">{totalLive}</span>
              <span className="text-xs text-[#94A3B8]">live</span>
            </div>
            <div className="flex items-center gap-1.5 bg-[#0F172A]/80 border border-[#1E293B] rounded-full px-3 py-1.5">
              <span className="text-xs font-semibold text-[#38BDF8]">{totalUpcoming}</span>
              <span className="text-xs text-[#94A3B8]">upcoming</span>
            </div>
            <div className="flex items-center gap-1.5 bg-[#0F172A]/80 border border-[#1E293B] rounded-full px-3 py-1.5">
              <span className="text-xs font-semibold text-[#22C55E]">{leagues.length}</span>
              <span className="text-xs text-[#94A3B8]">competitions</span>
            </div>
          </div>
        </div>
      </header>

      <QuickAccessBar />

      <section className="px-4 py-5">
        <h2 className="text-xs font-bold text-[#94A3B8] uppercase tracking-widest mb-3 px-1">
          Competitions
        </h2>
        <div className="grid gap-2.5">
          {leagues.length === 0 ? (
            <div className="text-center py-12 text-[#94A3B8]">
              <p className="text-4xl mb-3">⚽</p>
              <p className="text-sm">No leagues loaded yet. Start the backend to populate data.</p>
            </div>
          ) : (
            leagues.map((league) => <LeagueCard key={league.id} league={league} />)
          )}
        </div>
      </section>

      <footer className="px-4 py-6 border-t border-[#1E293B] text-[10px] text-[#94A3B8] text-center">
        Predictions are not guaranteed. Bet responsibly. 18+
      </footer>
    </main>
  );
}
