interface Props {
  label: string;
  value: string | number;
  color?: string;
  accent?: boolean;
}

export default function MetricPill({ label, value, color, accent }: Props) {
  return (
    <div className={`flex flex-col items-center px-3 py-2 rounded-lg ${
      accent ? "bg-[#0F172A] border border-[#1E293B]" : "bg-[#0F172A]"
    }`}>
      <span className="text-[10px] text-[#94A3B8] uppercase tracking-wide leading-none">{label}</span>
      <span
        className="text-base font-black leading-tight mt-0.5"
        style={{ color: color ?? "#F8FAFC" }}
      >
        {value}
      </span>
    </div>
  );
}
