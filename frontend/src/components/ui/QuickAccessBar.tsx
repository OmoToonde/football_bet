"use client";
import Link from "next/link";

const SHORTCUTS = [
  { label: "🔴 Live",        href: "/live" },
  { label: "⭐ Top Picks",  href: "/picks/high-confidence" },
  { label: "💰 Value",      href: "/picks/value-bets" },
  { label: "🏆 UCL",        href: "/league/champions-league" },
];

export default function QuickAccessBar() {
  return (
    <div className="flex gap-2 px-4 py-3 overflow-x-auto border-b border-[#1E293B] scrollbar-none">
      {SHORTCUTS.map((s) => (
        <Link key={s.href} href={s.href} className="shrink-0">
          <span className="text-xs font-medium px-3 py-1.5 rounded-full bg-[#0F172A] border border-[#1E293B] text-[#94A3B8] hover:border-[#22C55E]/60 hover:text-[#F8FAFC] transition-colors whitespace-nowrap">
            {s.label}
          </span>
        </Link>
      ))}
    </div>
  );
}
