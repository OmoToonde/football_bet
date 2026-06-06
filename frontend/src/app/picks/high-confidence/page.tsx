import { api } from "@/lib/api";
import PageHeader from "@/components/ui/PageHeader";
import PickRow from "@/components/prediction/PickRow";

export const revalidate = 60;

export default async function HighConfidencePage() {
  const { predictions } = await api.getHighConfidence().catch(() => ({ predictions: [] }));

  return (
    <div className="flex flex-col min-h-full">
      <PageHeader title="High Confidence Picks" subtitle="Model confidence ≥ 65% · Fresh data only" icon="⭐" />
      <div className="flex-1 px-3 py-3">
        {predictions.length === 0 ? (
          <div className="text-center py-12 text-[#94A3B8]">
            <p className="text-4xl mb-3">⭐</p>
            <p className="font-medium">No high-confidence picks right now</p>
            <p className="text-sm mt-1">Check back closer to matchday</p>
          </div>
        ) : (
          <div className="bg-[#111827] border border-[#1E293B] rounded-xl overflow-hidden divide-y divide-[#1E293B]">
            {predictions.map((p) => <PickRow key={p.id} pred={p} metric="confidence" />)}
          </div>
        )}
      </div>
      <footer className="px-4 py-3 text-center text-[10px] text-[#94A3B8] border-t border-[#1E293B]">
        Predictions are not guaranteed. Bet responsibly. 18+
      </footer>
    </div>
  );
}
