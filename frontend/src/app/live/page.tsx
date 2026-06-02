import { api } from "@/lib/api";
import MatchCard from "@/components/match/MatchCard";
import PageHeader from "@/components/ui/PageHeader";

export const revalidate = 10;

export default async function LivePage() {
  const { matches } = await api.getLiveMatches().catch(() => ({ matches: [] }));

  return (
    <div className="flex flex-col min-h-full">
      <PageHeader title="Live Now" subtitle="In-play matches with real-time insights" />

      <div className="flex-1 px-4 py-4">
        {matches.length === 0 ? (
          <div className="text-center py-16 text-[#94A3B8]">
            <p className="text-5xl mb-4">🔴</p>
            <p className="font-medium text-[#F8FAFC]">No live matches right now</p>
            <p className="text-sm mt-2">Live recommendations appear here during matches</p>
            <p className="text-xs mt-4 text-[#94A3B8]/70">
              Live bets carry elevated risk — odds change within seconds.
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            <p className="text-xs text-[#EF4444] font-medium mb-3 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-[#EF4444] animate-pulse" />
              Live High Risk · Predictions update in real-time
            </p>
            {matches.map((m) => <MatchCard key={m.id} match={m} />)}
          </div>
        )}
      </div>

      <footer className="px-4 py-3 text-center text-[10px] text-[#94A3B8] border-t border-[#1E293B]">
        Live betting is high risk. Predictions are not guaranteed. Bet responsibly. 18+
      </footer>
    </div>
  );
}
