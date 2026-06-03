interface SimulationData {
  simulations: number;
  winner: Record<string, number>;
  final: Record<string, number>;
  semi_final: Record<string, number>;
  quarter_final: Record<string, number>;
  round_of_16: Record<string, number>;
  league_phase_top_8: Record<string, number>;
}

interface Props { simulation: SimulationData; }

const STAGE_LABELS: Array<{ key: keyof SimulationData; label: string; color: string }> = [
  { key: "winner",            label: "Win trophy",   color: "#F59E0B" },
  { key: "final",             label: "Reach final",  color: "#22C55E" },
  { key: "semi_final",        label: "Semi-final",   color: "#38BDF8" },
  { key: "quarter_final",     label: "Quarter-final", color: "#94A3B8" },
];

function TeamRow({ team, probs, max }: { team: string; probs: number[]; max: number }) {
  return (
    <div className="flex items-center gap-2 py-1.5 border-t border-[#1E293B] first:border-0">
      <span className="text-xs text-[#F8FAFC] w-36 shrink-0 truncate">{team}</span>
      {probs.map((p, i) => {
        const pct = Math.round(p * 100);
        const barW = max > 0 ? Math.round((p / max) * 100) : 0;
        return (
          <div key={i} className="flex-1">
            <div className="h-1.5 bg-[#1E293B] rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all"
                style={{
                  width: `${barW}%`,
                  backgroundColor: STAGE_LABELS[i]?.color ?? "#94A3B8",
                }}
              />
            </div>
            <p className="text-[10px] text-[#94A3B8] text-center mt-0.5">{pct}%</p>
          </div>
        );
      })}
    </div>
  );
}

export default function TournamentSimulation({ simulation }: Props) {
  const winner = simulation.winner as Record<string, number>;
  const topTeams = Object.keys(winner).slice(0, 16);

  const maxWin = Math.max(...Object.values(winner));

  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-xs font-semibold text-[#94A3B8] uppercase tracking-widest">
          Tournament Simulation
        </h2>
        <span className="text-[10px] text-[#94A3B8]">
          {(simulation.simulations / 1000).toFixed(0)}k Monte Carlo runs
        </span>
      </div>

      {/* Legend */}
      <div className="flex gap-3 flex-wrap">
        {STAGE_LABELS.map((s) => (
          <span key={s.key} className="flex items-center gap-1 text-[10px] text-[#94A3B8]">
            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: s.color }} />
            {s.label}
          </span>
        ))}
      </div>

      <div className="bg-[#111827] border border-[#1E293B] rounded-xl p-4">
        {/* Column headers */}
        <div className="flex items-center gap-2 pb-2">
          <span className="text-[10px] text-[#94A3B8] w-36 shrink-0">Team</span>
          {STAGE_LABELS.map((s) => (
            <span key={s.key} className="flex-1 text-[10px] text-center" style={{ color: s.color }}>
              {s.label.split(" ")[0]}
            </span>
          ))}
        </div>

        {topTeams.map((team) => (
          <TeamRow
            key={team}
            team={team}
            probs={STAGE_LABELS.map((s) => (simulation[s.key] as Record<string, number>)[team] ?? 0)}
            max={maxWin}
          />
        ))}
      </div>

      <p className="text-[10px] text-[#94A3B8] text-center">
        Based on UEFA coefficients and domestic strength ratings.
        Predictions are not guaranteed.
      </p>
    </section>
  );
}
