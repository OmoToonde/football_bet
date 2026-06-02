import { type ScorelineProbability } from "@/lib/api";

interface Props {
  scorelines: ScorelineProbability[];
  homeTeam: string;
  awayTeam: string;
}

export default function ScorelineProbabilities({ scorelines, homeTeam, awayTeam }: Props) {
  const top = scorelines.slice(0, 6);
  const max = top[0]?.probability ?? 1;

  // Abbreviate team names — use first word unless both teams share the same first word
  const homeWords = homeTeam.split(" ");
  const awayWords = awayTeam.split(" ");
  const homeShort = homeWords[0] === awayWords[0]
    ? homeTeam.slice(0, 8)
    : homeWords[0];
  const awayShort = awayWords[awayWords.length - 1] === homeWords[homeWords.length - 1]
    ? awayWords[0]
    : awayWords[0];

  return (
    <div className="space-y-1.5">
      <p className="text-xs font-semibold text-[#94A3B8] uppercase tracking-wide mb-2">
        Top Scorelines
      </p>
      {top.map((s) => {
        const label = `${homeShort} ${s.home_goals}–${s.away_goals} ${awayShort}`;
        const pct = Math.round(s.probability * 100);
        const barWidth = Math.round((s.probability / max) * 100);

        return (
          <div key={`${s.home_goals}-${s.away_goals}`} className="flex items-center gap-2">
            <span className="text-xs text-[#F8FAFC] w-32 shrink-0">{label}</span>
            <div className="flex-1 bg-[#1E293B] rounded-full h-1.5">
              <div
                className="bg-[#38BDF8] h-1.5 rounded-full transition-all"
                style={{ width: `${barWidth}%` }}
              />
            </div>
            <span className="text-xs text-[#94A3B8] w-8 text-right">{pct}%</span>
          </div>
        );
      })}
    </div>
  );
}
