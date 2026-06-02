"use client";

const STYLES: Record<string, string> = {
  Fresh:          "text-[#22C55E] border-[#22C55E]/40",
  Acceptable:     "text-[#38BDF8] border-[#38BDF8]/40",
  Incomplete:     "text-[#F59E0B] border-[#F59E0B]/40",
  Stale:          "text-[#F97316] border-[#F97316]/40",
  Blocked:        "text-[#EF4444] border-[#EF4444]/40",
  "Live Delayed": "text-[#EF4444] border-[#EF4444]/40",
};

function timeAgo(iso: string): string {
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return `${Math.floor(diff / 3600)}h ago`;
}

export default function FreshnessBadge({ status, updatedAt }: { status: string; updatedAt: string }) {
  const style = STYLES[status] ?? "text-[#94A3B8] border-[#94A3B8]/40";
  return (
    <span className={`inline-flex items-center gap-1.5 text-[10px] border rounded-full px-2 py-0.5 ${style}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current" />
      {status} · {timeAgo(updatedAt)}
    </span>
  );
}
