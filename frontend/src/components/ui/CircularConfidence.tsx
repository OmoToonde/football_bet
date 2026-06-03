interface Props {
  value: number;   // 0-100
  size?: number;
  strokeWidth?: number;
}

export default function CircularConfidence({ value, size = 72, strokeWidth = 6 }: Props) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const filled = (value / 100) * circumference;
  const color =
    value >= 70 ? "#22C55E" :
    value >= 55 ? "#38BDF8" :
    value >= 40 ? "#F59E0B" : "#EF4444";

  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        {/* Track */}
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none" stroke="#1E293B" strokeWidth={strokeWidth}
        />
        {/* Progress */}
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none" stroke={color} strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={circumference - filled}
          style={{ transition: "stroke-dashoffset 0.6s ease" }}
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="text-base font-black leading-none" style={{ color }}>
          {Math.round(value)}
        </span>
        <span className="text-[8px] text-[#94A3B8] leading-none mt-0.5">%</span>
      </div>
    </div>
  );
}
