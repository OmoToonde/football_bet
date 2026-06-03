import PageHeader from "@/components/ui/PageHeader";

export const revalidate = 300;

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function fetchPerf<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${API}${path}`, { next: { revalidate: 300 } });
    if (!res.ok) return null;
    return res.json();
  } catch { return null; }
}

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="bg-[#111827] border border-[#1E293B] rounded-2xl p-4 text-center card-hover">
      <p className="text-[10px] text-[#94A3B8] uppercase tracking-wide">{label}</p>
      <p className="text-2xl font-black text-[#F8FAFC] mt-1">{value}</p>
      {sub && <p className="text-xs text-[#94A3B8] mt-0.5">{sub}</p>}
    </div>
  );
}

function CalibrationBar({ stated, actual, bracket }: { stated: number; actual: number; bracket: string }) {
  const gap = stated - actual;
  const color = Math.abs(gap) < 5 ? "#22C55E" : Math.abs(gap) < 12 ? "#F59E0B" : "#EF4444";
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-[#94A3B8]">{bracket}</span>
        <span style={{ color }}>
          Actual {actual}% {gap !== 0 ? `(${gap > 0 ? "over" : "under"} by ${Math.abs(gap).toFixed(1)}pp)` : "(perfect)"}
        </span>
      </div>
      <div className="relative h-2 bg-[#1E293B] rounded-full overflow-hidden">
        {/* Stated confidence */}
        <div className="absolute inset-y-0 left-0 bg-[#1E293B] rounded-full"
          style={{ width: `${stated}%` }} />
        {/* Actual win rate */}
        <div className="absolute inset-y-0 left-0 rounded-full transition-all"
          style={{ width: `${actual}%`, backgroundColor: color }} />
      </div>
    </div>
  );
}

export default async function PerformancePage() {
  const [overview, leagues, betTypes, calibration, roi] = await Promise.all([
    fetchPerf<any>("/performance/overview"),
    fetchPerf<any>("/performance/by-league"),
    fetchPerf<any>("/performance/by-bet-type"),
    fetchPerf<any>("/performance/calibration"),
    fetchPerf<any>("/performance/roi"),
  ]);

  const noData = !overview || overview.total_predictions === 0;

  return (
    <div className="flex flex-col min-h-full">
      <PageHeader
        title="Model Performance"
        subtitle="Prediction accuracy, calibration, and ROI simulation"
      />

      <div className="flex-1 px-4 py-4 space-y-6">
        {noData ? (
          <div className="text-center py-12 text-[#94A3B8]">
            <p className="text-4xl mb-3">📊</p>
            <p className="font-medium">No performance data yet</p>
            <p className="text-sm mt-1">Evaluations run automatically after matches finish</p>
          </div>
        ) : (
          <>
            {/* Overview */}
            <section>
              <h2 className="text-xs font-semibold text-[#94A3B8] uppercase tracking-widest mb-3">Overview</h2>
              <div className="grid grid-cols-2 gap-2">
                <StatCard label="Predictions" value={overview.total_predictions} />
                <StatCard label="Winner Accuracy" value={`${overview.winner_accuracy}%`} />
                <StatCard label="Exact Score" value={`${overview.exact_score_accuracy}%`} />
                <StatCard label="Avg Goal Error" value={`±${overview.avg_goal_margin_error}`} sub="goals" />
              </div>
            </section>

            {/* ROI */}
            {roi && (
              <section>
                <h2 className="text-xs font-semibold text-[#94A3B8] uppercase tracking-widest mb-3">
                  ROI Simulation (flat 1-unit stake)
                </h2>
                <div className="grid grid-cols-2 gap-2">
                  <div className="bg-[#111827] border border-[#1E293B] rounded-xl p-4">
                    <p className="text-[10px] text-[#94A3B8] uppercase tracking-wide">All Bets</p>
                    <p className={`text-2xl font-black mt-1 ${roi.all_bets.roi_pct >= 0 ? "text-[#22C55E]" : "text-[#EF4444]"}`}>
                      {roi.all_bets.roi_pct > 0 ? "+" : ""}{roi.all_bets.roi_pct}%
                    </p>
                    <p className="text-xs text-[#94A3B8] mt-0.5">{roi.all_bets.wins}/{roi.all_bets.total} wins</p>
                  </div>
                  <div className="bg-[#111827] border border-[#1E293B] rounded-xl p-4">
                    <p className="text-[10px] text-[#F59E0B] uppercase tracking-wide">Value Bets Only</p>
                    <p className={`text-2xl font-black mt-1 ${roi.value_bets_only.roi_pct >= 0 ? "text-[#22C55E]" : "text-[#EF4444]"}`}>
                      {roi.value_bets_only.roi_pct > 0 ? "+" : ""}{roi.value_bets_only.roi_pct}%
                    </p>
                    <p className="text-xs text-[#94A3B8] mt-0.5">{roi.value_bets_only.wins}/{roi.value_bets_only.total} wins</p>
                  </div>
                </div>
              </section>
            )}

            {/* Confidence calibration */}
            {calibration?.calibration?.length > 0 && (
              <section>
                <h2 className="text-xs font-semibold text-[#94A3B8] uppercase tracking-widest mb-3">
                  Confidence Calibration
                </h2>
                <div className="bg-[#111827] border border-[#1E293B] rounded-xl p-4 space-y-3">
                  <p className="text-xs text-[#94A3B8]">
                    A well-calibrated model's stated confidence should match its actual win rate.
                  </p>
                  {calibration.calibration.map((c: any) => (
                    <CalibrationBar
                      key={c.confidence_bracket}
                      bracket={c.confidence_bracket}
                      stated={c.stated_confidence_mid}
                      actual={c.actual_win_rate}
                    />
                  ))}
                </div>
              </section>
            )}

            {/* By league */}
            {leagues?.leagues?.length > 0 && (
              <section>
                <h2 className="text-xs font-semibold text-[#94A3B8] uppercase tracking-widest mb-3">By League</h2>
                <div className="bg-[#111827] border border-[#1E293B] rounded-xl overflow-hidden">
                  {leagues.leagues.map((l: any, i: number) => (
                    <div key={l.league}
                      className={`flex items-center justify-between px-4 py-3 ${i > 0 ? "border-t border-[#1E293B]" : ""}`}>
                      <span className="text-sm font-medium text-[#F8FAFC]">{l.league}</span>
                      <div className="flex gap-4 text-xs text-[#94A3B8]">
                        <span>Winner <span className="text-[#F8FAFC] font-semibold">{l.winner_accuracy}%</span></span>
                        <span>Bet <span className="text-[#F8FAFC] font-semibold">{l.bet_win_rate}%</span></span>
                        <span className={l.roi_units >= 0 ? "text-[#22C55E]" : "text-[#EF4444]"}>
                          {l.roi_units >= 0 ? "+" : ""}{l.roi_units}u
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* By bet type */}
            {betTypes?.bet_types?.length > 0 && (
              <section>
                <h2 className="text-xs font-semibold text-[#94A3B8] uppercase tracking-widest mb-3">By Bet Type</h2>
                <div className="bg-[#111827] border border-[#1E293B] rounded-xl overflow-hidden">
                  {betTypes.bet_types.map((b: any, i: number) => (
                    <div key={b.bet_type}
                      className={`flex items-center justify-between px-4 py-3 ${i > 0 ? "border-t border-[#1E293B]" : ""}`}>
                      <span className="text-xs text-[#F8FAFC] flex-1 pr-2">{b.bet_type}</span>
                      <div className="flex gap-3 text-xs text-[#94A3B8] shrink-0">
                        <span>{b.total} preds</span>
                        <span><span className="text-[#F8FAFC] font-semibold">{b.win_rate}%</span> win</span>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            )}
          </>
        )}
      </div>

      <footer className="px-4 py-3 text-center text-[10px] text-[#94A3B8] border-t border-[#1E293B]">
        Past performance does not guarantee future results. Bet responsibly. 18+
      </footer>
    </div>
  );
}
