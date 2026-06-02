interface Props {
  homeTeam: string;
  awayTeam: string;
  homeProb: number;
  drawProb: number;
  awayProb: number;
}

export default function ProbabilityBar({ homeTeam, awayTeam, homeProb, drawProb, awayProb }: Props) {
  const h = Math.round(homeProb * 100);
  const d = Math.round(drawProb * 100);
  const a = Math.round(awayProb * 100);

  return (
    <div className="space-y-2">
      <div className="flex justify-between text-xs text-[#94A3B8]">
        <span className="truncate max-w-[40%]">{homeTeam}</span>
        <span>Draw</span>
        <span className="truncate max-w-[40%] text-right">{awayTeam}</span>
      </div>
      <div className="flex h-7 rounded-lg overflow-hidden gap-0.5">
        <div
          className="bg-[#22C55E] flex items-center justify-center text-xs font-bold text-[#07111F] transition-all"
          style={{ width: `${h}%` }}
        >
          {h >= 12 ? `${h}%` : ""}
        </div>
        <div
          className="bg-[#94A3B8] flex items-center justify-center text-xs font-bold text-[#07111F] transition-all"
          style={{ width: `${d}%` }}
        >
          {d >= 10 ? `${d}%` : ""}
        </div>
        <div
          className="bg-[#38BDF8] flex items-center justify-center text-xs font-bold text-[#07111F] transition-all"
          style={{ width: `${a}%` }}
        >
          {a >= 12 ? `${a}%` : ""}
        </div>
      </div>
    </div>
  );
}
