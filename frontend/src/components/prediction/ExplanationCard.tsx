interface StructuredExplanation {
  main_reasoning: string;
  positive_factors: string[];
  risk_factors: string[];
  bet_rationale: string;
  rejected_markets: string[];
  data_note: string;
  no_bet_reason: string;
  is_live: boolean;
  live_note: string;
  disclaimer: string;
}

interface Props {
  explanation: string;            // plain-text fallback
  explanationJson: string | null; // JSON string of StructuredExplanation
}

function parseJson(raw: string | null): StructuredExplanation | null {
  if (!raw) return null;
  try { return JSON.parse(raw); } catch { return null; }
}

export default function ExplanationCard({ explanation, explanationJson }: Props) {
  const structured = parseJson(explanationJson);

  // Use structured display if available, plain text otherwise
  if (!structured) {
    return (
      <div className="bg-[#111827] border border-[#1E293B] rounded-xl p-4 space-y-2">
        <p className="text-[10px] text-[#94A3B8] uppercase tracking-wide font-semibold">AI Analysis</p>
        <p className="text-sm text-[#94A3B8] leading-relaxed">{explanation}</p>
      </div>
    );
  }

  return (
    <div className="bg-[#111827] border border-[#1E293B] rounded-xl p-4 space-y-4">
      <p className="text-[10px] text-[#94A3B8] uppercase tracking-wide font-semibold">AI Analysis</p>

      {/* Main reasoning */}
      <p className="text-sm text-[#F8FAFC] leading-relaxed">{structured.main_reasoning}</p>

      {/* Bet rationale */}
      {structured.bet_rationale && (
        <p className="text-sm text-[#94A3B8] leading-relaxed border-l-2 border-[#22C55E] pl-3">
          {structured.bet_rationale}
        </p>
      )}

      {/* No bet reason */}
      {structured.no_bet_reason && (
        <p className="text-sm text-[#F97316] leading-relaxed border-l-2 border-[#F97316] pl-3">
          {structured.no_bet_reason}
        </p>
      )}

      {/* Positives */}
      {structured.positive_factors.length > 0 && (
        <div className="space-y-1.5">
          <p className="text-[10px] font-semibold text-[#22C55E] uppercase tracking-wide">
            Positive signals
          </p>
          <ul className="space-y-1">
            {structured.positive_factors.map((f, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-[#94A3B8]">
                <span className="text-[#22C55E] mt-0.5 shrink-0">+</span>
                <span>{f}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Risks */}
      {structured.risk_factors.length > 0 && (
        <div className="space-y-1.5">
          <p className="text-[10px] font-semibold text-[#F97316] uppercase tracking-wide">
            Risk factors
          </p>
          <ul className="space-y-1">
            {structured.risk_factors.map((r, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-[#94A3B8]">
                <span className="text-[#F97316] mt-0.5 shrink-0">!</span>
                <span>{r}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Markets considered */}
      {structured.rejected_markets.length > 0 && (
        <details className="group">
          <summary className="text-[10px] text-[#94A3B8] cursor-pointer hover:text-[#F8FAFC] transition-colors select-none">
            Markets considered ▾
          </summary>
          <ul className="mt-2 space-y-1">
            {structured.rejected_markets.map((m, i) => (
              <li key={i} className="text-xs text-[#94A3B8] pl-3">– {m}</li>
            ))}
          </ul>
        </details>
      )}

      {/* Data note */}
      {structured.data_note && (
        <p className="text-[10px] text-[#94A3B8] border-t border-[#1E293B] pt-3">
          {structured.data_note}
        </p>
      )}

      {/* Live note */}
      {structured.live_note && (
        <p className="text-xs text-[#EF4444] border-t border-[#1E293B] pt-3">
          {structured.live_note}
        </p>
      )}

      {/* Disclaimer */}
      <p className="text-[10px] text-[#94A3B8]/60 border-t border-[#1E293B] pt-2">
        {structured.disclaimer}
      </p>
    </div>
  );
}
