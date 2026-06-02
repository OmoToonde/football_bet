const STYLES: Record<string, string> = {
  "Low":               "bg-[#166534]/50 text-[#22C55E]",
  "Medium":            "bg-[#78350f]/50 text-[#F59E0B]",
  "High":              "bg-[#7c2d12]/50 text-[#F97316]",
  "Very High":         "bg-[#7f1d1d]/50 text-[#EF4444]",
  "Live High Risk":    "bg-[#7f1d1d]/60 text-[#EF4444] animate-pulse",
  "No Bet Recommended":"bg-[#1E293B] text-[#94A3B8]",
};

export default function RiskBadge({ level }: { level: string }) {
  return (
    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${STYLES[level] ?? "bg-[#1E293B] text-[#94A3B8]"}`}>
      {level}
    </span>
  );
}
