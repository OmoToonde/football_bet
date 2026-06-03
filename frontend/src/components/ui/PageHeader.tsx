import Link from "next/link";

interface Props {
  title: string;
  subtitle?: string;
  backHref?: string;
  backLabel?: string;
  icon?: string;
}

export default function PageHeader({ title, subtitle, backHref, backLabel, icon }: Props) {
  return (
    <header className="relative overflow-hidden px-5 pt-5 pb-4 border-b border-[#1E293B]">
      <div
        className="absolute -top-20 -right-12 w-48 h-48 rounded-full opacity-10 blur-3xl pointer-events-none"
        style={{ background: "radial-gradient(circle, #22C55E 0%, transparent 70%)" }}
      />
      <div className="relative">
        {backHref && (
          <Link href={backHref} className="inline-flex items-center gap-1 text-[#94A3B8] text-sm mb-3 hover:text-[#F8FAFC] transition-colors">
            <span>←</span>
            <span>{backLabel ?? "Back"}</span>
          </Link>
        )}
        <div className="flex items-center gap-2">
          {icon && <span className="text-xl">{icon}</span>}
          <h1 className="text-xl font-black tracking-tight text-[#F8FAFC]">{title}</h1>
        </div>
        {subtitle && <p className="text-sm text-[#94A3B8] mt-0.5">{subtitle}</p>}
      </div>
    </header>
  );
}
