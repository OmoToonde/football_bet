import { api, type Prediction } from "@/lib/api";
import PageHeader from "@/components/ui/PageHeader";
import RiskBadge from "@/components/ui/RiskBadge";
import FreshnessBadge from "@/components/ui/FreshnessBadge";
import Link from "next/link";

export const revalidate = 60;

function PredCard({ p }: { p: Prediction }) {
  return (
    <Link href={`/league/unknown/${p.match_id}`}>
      <div className="bg-[#111827] border border-[#1E293B] rounded-xl p-4 space-y-2 hover:border-[#22C55E]/50 transition-colors">
        <div className="flex items-start justify-between">
          <p className="text-[#22C55E] font-semibold text-sm flex-1 pr-2">{p.recommended_bet}</p>
          <RiskBadge level={p.risk_level} />
        </div>
        <div className="flex items-center gap-4 text-sm">
          <span className="text-[#94A3B8]">Confidence <span className="text-[#F8FAFC] font-bold">{p.confidence_score?.toFixed(0)}%</span></span>
          {p.expected_score && (
            <span className="text-[#94A3B8]">Score <span className="text-[#38BDF8] font-medium">{p.expected_score}</span></span>
          )}
        </div>
        <FreshnessBadge status={p.data_freshness_status} updatedAt={p.generated_at} />
      </div>
    </Link>
  );
}

export default async function HighConfidencePage() {
  const { predictions } = await api.getHighConfidence().catch(() => ({ predictions: [] }));

  return (
    <div className="flex flex-col min-h-full">
      <PageHeader
        title="High Confidence Picks"
        subtitle="Model confidence ≥ 65% · Fresh data only"
      />
      <div className="flex-1 px-4 py-4">
        {predictions.length === 0 ? (
          <div className="text-center py-12 text-[#94A3B8]">
            <p className="text-4xl mb-3">⭐</p>
            <p className="font-medium">No high-confidence picks right now</p>
            <p className="text-sm mt-1">Check back closer to matchday</p>
          </div>
        ) : (
          <div className="space-y-3">
            {predictions.map((p) => <PredCard key={p.id} p={p} />)}
          </div>
        )}
      </div>
      <footer className="px-4 py-3 text-center text-[10px] text-[#94A3B8] border-t border-[#1E293B]">
        Predictions are not guaranteed. Bet responsibly. 18+
      </footer>
    </div>
  );
}
