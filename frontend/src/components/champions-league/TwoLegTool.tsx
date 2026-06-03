"use client";
import { useState } from "react";

interface CLTeam { name: string; league: string; domestic_strength: number; seed: number; }

interface TwoLegResult {
  home_team: string;
  away_team: string;
  home_qualify_probability: number;
  away_qualify_probability: number;
  extra_time_probability: number;
  penalty_probability: number;
  first_leg_played: boolean;
  narrative: string;
}

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function TwoLegTool({ teams }: { teams: CLTeam[] }) {
  const [homeTeam, setHomeTeam] = useState(teams[0]?.name ?? "");
  const [awayTeam, setAwayTeam] = useState(teams[4]?.name ?? "");
  const [leg1Home, setLeg1Home] = useState("");
  const [leg1Away, setLeg1Away] = useState("");
  const [result, setResult] = useState<TwoLegResult | null>(null);
  const [loading, setLoading] = useState(false);

  const homeInfo = teams.find((t) => t.name === homeTeam);
  const awayInfo = teams.find((t) => t.name === awayTeam);

  async function predict() {
    if (!homeInfo || !awayInfo) return;
    setLoading(true);
    try {
      const body: Record<string, unknown> = {
        home_team: homeInfo.name,
        home_strength: homeInfo.domestic_strength,
        home_league: homeInfo.league,
        away_team: awayInfo.name,
        away_strength: awayInfo.domestic_strength,
        away_league: awayInfo.league,
      };
      if (leg1Home !== "" && leg1Away !== "") {
        body.first_leg_home_score = Number(leg1Home);
        body.first_leg_away_score = Number(leg1Away);
      }
      const res = await fetch(`${API}/cl/two-leg-prediction`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (res.ok) setResult(await res.json());
    } catch {}
    setLoading(false);
  }

  const selectClass = "bg-[#0F172A] border border-[#1E293B] rounded-lg px-3 py-2 text-sm text-[#F8FAFC] w-full focus:outline-none focus:border-[#22C55E] transition-colors";
  const inputClass  = "bg-[#0F172A] border border-[#1E293B] rounded-lg px-3 py-2 text-sm text-[#F8FAFC] w-full text-center focus:outline-none focus:border-[#22C55E] transition-colors";

  return (
    <section className="space-y-3">
      <h2 className="text-xs font-semibold text-[#94A3B8] uppercase tracking-widest">
        Two-Leg Tie Predictor
      </h2>
      <div className="bg-[#111827] border border-[#1E293B] rounded-xl p-4 space-y-4">

        {/* Team selects */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <p className="text-[10px] text-[#94A3B8] mb-1">Home (1st leg)</p>
            <select value={homeTeam} onChange={(e) => setHomeTeam(e.target.value)} className={selectClass}>
              {teams.map((t) => <option key={t.name} value={t.name}>{t.name}</option>)}
            </select>
          </div>
          <div>
            <p className="text-[10px] text-[#94A3B8] mb-1">Away (1st leg)</p>
            <select value={awayTeam} onChange={(e) => setAwayTeam(e.target.value)} className={selectClass}>
              {teams.map((t) => <option key={t.name} value={t.name}>{t.name}</option>)}
            </select>
          </div>
        </div>

        {/* Optional first-leg score */}
        <div>
          <p className="text-[10px] text-[#94A3B8] mb-1">First leg score (optional)</p>
          <div className="grid grid-cols-3 gap-2 items-center">
            <input
              type="number" min="0" max="20" placeholder="0"
              value={leg1Home} onChange={(e) => setLeg1Home(e.target.value)}
              className={inputClass}
            />
            <p className="text-center text-[#94A3B8] text-sm font-bold">–</p>
            <input
              type="number" min="0" max="20" placeholder="0"
              value={leg1Away} onChange={(e) => setLeg1Away(e.target.value)}
              className={inputClass}
            />
          </div>
        </div>

        {/* Submit */}
        <button
          onClick={predict}
          disabled={loading || homeTeam === awayTeam}
          className="w-full py-2.5 rounded-lg bg-[#16A34A] text-white text-sm font-semibold
                     hover:bg-[#15803d] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? "Simulating…" : "Simulate Tie (50k runs)"}
        </button>

        {/* Result */}
        {result && (
          <div className="space-y-3 border-t border-[#1E293B] pt-3">
            <div className="grid grid-cols-2 gap-3">
              {[
                { team: result.home_team, prob: result.home_qualify_probability },
                { team: result.away_team, prob: result.away_qualify_probability },
              ].map(({ team, prob }) => {
                const pct = Math.round(prob * 100);
                const color = pct >= 60 ? "#22C55E" : pct >= 40 ? "#F59E0B" : "#EF4444";
                return (
                  <div key={team} className="bg-[#0F172A] rounded-lg p-3 text-center">
                    <p className="text-xs text-[#94A3B8] truncate">{team}</p>
                    <p className="text-2xl font-black mt-1" style={{ color }}>{pct}%</p>
                    <p className="text-[10px] text-[#94A3B8]">qualify</p>
                  </div>
                );
              })}
            </div>

            <div className="flex gap-4 text-xs text-[#94A3B8] justify-center">
              <span>Extra time <span className="text-[#F8FAFC] font-semibold">{Math.round(result.extra_time_probability * 100)}%</span></span>
              <span>Penalties <span className="text-[#F8FAFC] font-semibold">{Math.round(result.penalty_probability * 100)}%</span></span>
            </div>

            <p className="text-xs text-[#94A3B8] leading-relaxed border-l-2 border-[#22C55E] pl-3">
              {result.narrative}
            </p>
            <p className="text-[10px] text-[#94A3B8]/60 text-center">
              Predictions are not guaranteed. Bet responsibly. 18+
            </p>
          </div>
        )}
      </div>
    </section>
  );
}
