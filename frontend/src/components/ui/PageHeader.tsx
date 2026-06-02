import Link from "next/link";

interface Props {
  title: string;
  subtitle?: string;
  backHref?: string;
  backLabel?: string;
}

export default function PageHeader({ title, subtitle, backHref, backLabel }: Props) {
  return (
    <header className="px-4 pt-5 pb-4 border-b border-[#1E293B]">
      {backHref && (
        <Link href={backHref} className="flex items-center gap-1 text-[#94A3B8] text-sm mb-3 hover:text-[#F8FAFC] transition-colors">
          <span>←</span>
          <span>{backLabel ?? "Back"}</span>
        </Link>
      )}
      <h1 className="text-xl font-bold text-[#F8FAFC]">{title}</h1>
      {subtitle && <p className="text-sm text-[#94A3B8] mt-0.5">{subtitle}</p>}
    </header>
  );
}
