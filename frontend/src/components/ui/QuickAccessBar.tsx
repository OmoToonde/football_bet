"use client";
import Link from "next/link";

const SHORTCUTS = [
  { label: "🔴 Live Now", href: "/live" },
  { label: "⭐ High Confidence", href: "/picks/high-confidence" },
  { label: "💰 Value Bets", href: "/picks/value-bets" },
  { label: "🏆 Champions League", href: "/league/champions-league" },
];

export default function QuickAccessBar() {
  return (
    <div className="flex gap-2 px-4 py-3 overflow-x-auto border-b border-[#1E293B]">
      {SHORTCUTS.map((s) => (
        <Link key={s.href} href={s.href}>
          <span className="whitespace-nowrap text-xs font-medium px-3 py-1.5 rounded-full bg-[#0F172A] border border-[#1E293B] text-[#94A3B8] hover:border-[#22C55E] hover:text-[#F8FAFC] transition-colors">
            {s.label}
          </span>
        </Link>
      ))}
    </div>
  );
}
