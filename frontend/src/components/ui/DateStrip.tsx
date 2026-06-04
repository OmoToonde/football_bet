"use client";
import { useState } from "react";

function buildDays(): { key: string; label: string; date: Date }[] {
  const out: { key: string; label: string; date: Date }[] = [];
  const today = new Date();
  for (let i = -3; i <= 3; i++) {
    const d = new Date(today);
    d.setDate(today.getDate() + i);
    let label: string;
    if (i === 0) label = "Today";
    else if (i === -1) label = "Yest";
    else if (i === 1) label = "Tmrw";
    else label = d.toLocaleDateString("en-GB", { weekday: "short" });
    out.push({ key: d.toISOString().slice(0, 10), label, date: d });
  }
  return out;
}

export default function DateStrip() {
  const days = buildDays();
  const [active, setActive] = useState(days[3].key); // today

  return (
    <div className="flex gap-1 px-3 py-2 overflow-x-auto scrollbar-none border-b border-[#1E293B] bg-[#0B1220]">
      {days.map((d) => {
        const isActive = d.key === active;
        return (
          <button
            key={d.key}
            onClick={() => setActive(d.key)}
            className={`flex flex-col items-center min-w-[52px] py-1.5 px-2 rounded-lg transition-colors ${
              isActive ? "bg-[#22C55E]/15" : "hover:bg-[#1A2232]"
            }`}
          >
            <span className={`text-[11px] font-semibold ${isActive ? "text-[#22C55E]" : "text-[#94A3B8]"}`}>
              {d.label}
            </span>
            <span className={`text-[10px] ${isActive ? "text-[#22C55E]" : "text-[#475569]"}`}>
              {d.date.getDate()}/{d.date.getMonth() + 1}
            </span>
          </button>
        );
      })}
    </div>
  );
}
