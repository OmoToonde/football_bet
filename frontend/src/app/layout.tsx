import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Football Intelligence",
  description: "AI-powered football betting insights. Not financial advice.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} antialiased`}
    >
      <body className="min-h-dvh flex flex-col bg-[#07111F] text-[#F8FAFC]">
        <div className="flex-1 flex flex-col max-w-2xl mx-auto w-full">
          {children}
        </div>
        <nav className="sticky bottom-0 bg-[#0F172A] border-t border-[#1E293B] max-w-2xl mx-auto w-full">
          <div className="flex justify-around py-2">
            {[
              { href: "/",                      label: "Home",    icon: "⚽" },
              { href: "/live",                  label: "Live",    icon: "🔴" },
              { href: "/picks/high-confidence", label: "Picks",   icon: "⭐" },
              { href: "/performance",           label: "Stats",   icon: "📊" },
            ].map(({ href, label, icon }) => (
              <a
                key={href}
                href={href}
                className="flex flex-col items-center gap-0.5 px-3 py-1 text-[#94A3B8] hover:text-[#22C55E] transition-colors"
              >
                <span className="text-lg leading-none">{icon}</span>
                <span className="text-[10px] font-medium">{label}</span>
              </a>
            ))}
          </div>
        </nav>
      </body>
    </html>
  );
}
