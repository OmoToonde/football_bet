const RISK_STYLES: Record<string, string> = {
  "Low":              "bg-[#166534] text-[#22C55E]",
  "Medium":           "bg-[#92400e] text-[#F59E0B]",
  "High":             "bg-[#7f1d1d] text-[#F97316]",
  "Very High":        "bg-[#7f1d1d] text-[#EF4444]",
  "Live High Risk":   "bg-[#7f1d1d] text-[#EF4444] animate-pulse",
  "No Bet Recommended": "bg-[#1E293B] text-[#94A3B8]",
};

export default function RiskBadge({ level }: { level: string }) {
  const style = RISK_STYLES[level] ?? "bg-[#1E293B] text-[#94A3B8]";
  return (
    <span className={`text-xs font-medium px-2 py-1 rounded-md ${style}`}>
      {level}
    </span>
  );
}
