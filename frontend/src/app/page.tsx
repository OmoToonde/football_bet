import { api } from "@/lib/api";
import LeagueCard from "@/components/league/LeagueCard";
import QuickAccessBar from "@/components/ui/QuickAccessBar";

export const revalidate = 60;

export default async function HomePage() {
  const { leagues } = await api.getLeagues().catch(() => ({ leagues: [] }));

  return (
    <main className="min-h-screen bg-[#07111F] text-[#F8FAFC]">
      <header className="px-4 py-6 border-b border-[#1E293B]">
        <h1 className="text-2xl font-bold text-[#22C55E]">Football Intelligence</h1>
        <p className="text-sm text-[#94A3B8] mt-1">
          AI-powered betting insights · Not financial advice
        </p>
      </header>

      <QuickAccessBar />

      <section className="px-4 py-6">
        <h2 className="text-lg font-semibold text-[#94A3B8] mb-4">Competitions</h2>
        <div className="grid gap-3">
          {leagues.length === 0 ? (
            <p className="text-[#94A3B8] text-sm">No leagues loaded yet. Start the backend to populate data.</p>
          ) : (
            leagues.map((league) => <LeagueCard key={league.id} league={league} />)
          )}
        </div>
      </section>

      <footer className="px-4 py-6 border-t border-[#1E293B] text-xs text-[#94A3B8]">
        Predictions are not guaranteed. Bet responsibly. 18+
      </footer>
    </main>
  );
}
