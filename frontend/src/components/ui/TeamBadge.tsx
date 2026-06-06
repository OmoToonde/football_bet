"use client";
import { useState } from "react";

// Deterministic colour per team name so each club keeps a consistent badge colour.
const PALETTE = [
  "#EF4444", "#F97316", "#F59E0B", "#22C55E", "#10B981",
  "#06B6D4", "#3B82F6", "#6366F1", "#8B5CF6", "#EC4899",
  "#14B8A6", "#84CC16", "#A855F7", "#0EA5E9", "#DC2626",
];

function colorFor(name: string): string {
  let h = 0;
  for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) >>> 0;
  return PALETTE[h % PALETTE.length];
}

function initials(name: string): string {
  const words = name.split(" ").filter((w) => w.length > 1 && !/^(fc|cf|ac|afc|sc)$/i.test(w));
  if (words.length === 0) return name.slice(0, 2).toUpperCase();
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase();
  return (words[0][0] + words[words.length - 1][0]).toUpperCase();
}

interface Props {
  name: string;
  logo?: string | null;
  size?: number;
}

export default function TeamBadge({ name, logo, size = 24 }: Props) {
  const [failed, setFailed] = useState(false);

  // Render the real crest when available and not errored
  if (logo && !failed) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={logo}
        alt={name}
        width={size}
        height={size}
        loading="lazy"
        onError={() => setFailed(true)}
        className="object-contain shrink-0"
        style={{ width: size, height: size }}
      />
    );
  }

  const color = colorFor(name);
  return (
    <span
      className="inline-flex items-center justify-center rounded-full font-bold shrink-0"
      style={{
        width: size, height: size,
        background: `${color}22`, color,
        border: `1.5px solid ${color}66`,
        fontSize: size * 0.38,
      }}
    >
      {initials(name)}
    </span>
  );
}
