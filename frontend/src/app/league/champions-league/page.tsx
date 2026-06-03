import PageHeader from "@/components/ui/PageHeader";
import TournamentSimulation from "@/components/champions-league/TournamentSimulation";
import TwoLegTool from "@/components/champions-league/TwoLegTool";

export const revalidate = 3600;

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function fetchSimulation() {
  try {
    const res = await fetch(`${API}/cl/simulation`, { next: { revalidate: 3600 } });
    if (!res.ok) return null;
    return res.json();
  } catch { return null; }
}

async function fetchTeams() {
  try {
    const res = await fetch(`${API}/cl/teams`, { next: { revalidate: 3600 } });
    if (!res.ok) return null;
    return res.json();
  } catch { return null; }
}

export default async function CLPage() {
  const [simulation, teams] = await Promise.all([fetchSimulation(), fetchTeams()]);

  return (
    <div className="flex flex-col min-h-full">
      <PageHeader
        title="Champions League"
        subtitle="AI tournament simulation · Cross-league strength · Two-leg predictions"
        backHref="/"
        backLabel="All Competitions"
      />

      {/* UCL badge */}
      <div className="px-4 py-3 bg-[#0F172A] border-b border-[#1E293B] flex items-center gap-3">
        <span className="text-3xl">🏆</span>
        <div>
          <p className="text-sm font-semibold text-[#F59E0B]">UEFA Champions League</p>
          <p className="text-xs text-[#94A3B8]">2025/26 Season · 36-team league phase</p>
        </div>
      </div>

      <div className="flex-1 px-4 py-4 space-y-6">
        {/* Tournament simulator */}
        {simulation ? (
          <TournamentSimulation simulation={simulation} />
        ) : (
          <div className="bg-[#111827] border border-[#1E293B] rounded-xl p-6 text-center text-[#94A3B8]">
            <p className="text-2xl mb-2">📊</p>
            <p className="text-sm">Tournament simulation unavailable — make sure the backend is running</p>
          </div>
        )}

        {/* Two-leg prediction tool */}
        <TwoLegTool teams={teams?.teams ?? []} />

        {/* Cross-league note */}
        <div className="bg-[#111827] border border-[#1E293B] rounded-xl p-4 space-y-2">
          <p className="text-xs font-semibold text-[#F59E0B] uppercase tracking-wide">How CL Predictions Work</p>
          <p className="text-xs text-[#94A3B8] leading-relaxed">
            Champions League predictions use UEFA league coefficients to adjust team strength
            across different domestic competitions. A Premier League side rated 0.75 domestically
            carries a higher adjusted rating than a Eredivisie side rated 0.75, because the
            Premier League has a stronger UEFA coefficient.
          </p>
          <p className="text-xs text-[#94A3B8] leading-relaxed">
            European experience, squad depth, travel distance, and knockout psychology
            are additional factors applied on top of domestic metrics.
          </p>
        </div>
      </div>

      <footer className="px-4 py-3 text-center text-[10px] text-[#94A3B8] border-t border-[#1E293B]">
        Predictions are not guaranteed. Bet responsibly. 18+
      </footer>
    </div>
  );
}
