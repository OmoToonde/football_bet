"use client";

const STATUS_STYLES: Record<string, string> = {
  Fresh:        "text-[#22C55E] border-[#22C55E]",
  Acceptable:   "text-[#38BDF8] border-[#38BDF8]",
  Incomplete:   "text-[#F59E0B] border-[#F59E0B]",
  Stale:        "text-[#F97316] border-[#F97316]",
  Blocked:      "text-[#EF4444] border-[#EF4444]",
  "Live Delayed": "text-[#EF4444] border-[#EF4444]",
};

function timeAgo(iso: string): string {
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return `${Math.floor(diff / 3600)}h ago`;
}

interface Props {
  status: string;
  updatedAt: string;
}

export default function FreshnessBadge({ status, updatedAt }: Props) {
  const style = STATUS_STYLES[status] ?? "text-[#94A3B8] border-[#94A3B8]";
  return (
    <span className={`inline-flex items-center gap-1.5 text-xs border rounded-full px-2 py-0.5 ${style}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current" />
      {status} · Updated {timeAgo(updatedAt)}
    </span>
  );
}
