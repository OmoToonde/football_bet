import { api, type Prediction } from "@/lib/api";
import PageHeader from "@/components/ui/PageHeader";
import RiskBadge from "@/components/ui/RiskBadge";
import FreshnessBadge from "@/components/ui/FreshnessBadge";
import Link from "next/link";

export const revalidate = 60;

function ValueCard({ p }: { p: Prediction }) {
  const ratingColor =
    p.value_rating >= 8 ? "text-[#22C55E]" :
    p.value_rating >= 6 ? "text-[#F59E0B]" : "text-[#94A3B8]";

  return (
    <Link href={`/league/unknown/${p.match_id}`}>
      <div className="bg-[#111827] border border-[#1E293B] rounded-xl p-4 space-y-2 hover:border-[#F59E0B]/50 transition-colors">
        <div className="flex items-start justify-between">
          <p className="text-[#F8FAFC] font-semibold text-sm flex-1 pr-2">{p.recommended_bet}</p>
          <span className={`text-lg font-black ${ratingColor}`}>
            {p.value_rating?.toFixed(1)}
            <span className="text-xs font-normal text-[#94A3B8]">/10</span>
          </span>
        </div>
        <div className="flex items-center gap-4 text-sm">
          <span className="text-[#94A3B8]">Confidence <span className="text-[#F8FAFC] font-bold">{p.confidence_score?.toFixed(0)}%</span></span>
          <RiskBadge level={p.risk_level} />
        </div>
        <FreshnessBadge status={p.data_freshness_status} updatedAt={p.generated_at} />
      </div>
    </Link>
  );
}

export default async function ValueBetsPage() {
  const { predictions } = await api.getValueBets().catch(() => ({ predictions: [] }));

  return (
    <div className="flex flex-col min-h-full">
      <PageHeader
        title="Value Bets"
        subtitle="Model probability exceeds bookmaker implied probability"
      />
      <div className="flex-1 px-4 py-4">
        {predictions.length === 0 ? (
          <div className="text-center py-12 text-[#94A3B8]">
            <p className="text-4xl mb-3">💰</p>
            <p className="font-medium">No value bets identified</p>
            <p className="text-sm mt-1">Value requires odds data — available once the season starts</p>
          </div>
        ) : (
          <div className="space-y-3">
            {predictions.map((p) => <ValueCard key={p.id} p={p} />)}
          </div>
        )}
      </div>
      <footer className="px-4 py-3 text-center text-[10px] text-[#94A3B8] border-t border-[#1E293B]">
        A higher value rating does not guarantee profit. Bet responsibly. 18+
      </footer>
    </div>
  );
}
