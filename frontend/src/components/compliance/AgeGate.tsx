"use client";
import { useState, useEffect } from "react";

const STORAGE_KEY = "fi_age_verified_v1";

export default function AgeGate() {
  const [accepted, setAccepted] = useState(true); // assume accepted until we read storage
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      setAccepted(stored === "true");
    } catch {
      setAccepted(false);
    }
  }, []);

  function accept() {
    try { localStorage.setItem(STORAGE_KEY, "true"); } catch {}
    setAccepted(true);
  }

  function decline() {
    // Send the user away — they have not confirmed they are of legal age
    window.location.href = "https://www.begambleaware.org/";
  }

  if (!mounted || accepted) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#07111F]/95 backdrop-blur-sm px-5">
      <div className="relative overflow-hidden bg-[#111827] border border-[#1E293B] rounded-2xl p-6 max-w-md w-full">
        <div
          className="absolute -top-20 -right-12 w-48 h-48 rounded-full opacity-15 blur-3xl pointer-events-none"
          style={{ background: "radial-gradient(circle, #22C55E 0%, transparent 70%)" }}
        />
        <div className="relative space-y-4">
          <div className="flex items-center gap-2">
            <span className="text-2xl">⚽</span>
            <h2 className="text-lg font-black gradient-text">Football Intelligence</h2>
          </div>

          <div className="space-y-3 text-sm text-[#94A3B8] leading-relaxed">
            <p className="text-[#F8FAFC] font-semibold">
              This app provides AI-powered football betting insights.
            </p>
            <p>
              Predictions are based on data and statistical models. They are
              <span className="text-[#F8FAFC] font-medium"> not guarantees</span>, and this is
              <span className="text-[#F8FAFC] font-medium"> not financial or betting advice</span>.
            </p>
            <p>
              You must be <span className="text-[#F8FAFC] font-medium">18 or older</span> (or the legal
              gambling age in your jurisdiction) to use this app.
            </p>
            <div className="bg-[#0F172A] border border-[#1E293B] rounded-xl p-3 space-y-1.5">
              <p className="text-xs text-[#94A3B8]">
                If gambling is affecting you or someone you know, support is available:
              </p>
              <a href="https://www.begambleaware.org/" target="_blank" rel="noopener noreferrer"
                className="text-xs text-[#38BDF8] underline block">
                BeGambleAware.org
              </a>
              <a href="https://www.gamcare.org.uk/" target="_blank" rel="noopener noreferrer"
                className="text-xs text-[#38BDF8] underline block">
                GamCare.org.uk · 0808 8020 133
              </a>
            </div>
          </div>

          <div className="flex flex-col gap-2 pt-2">
            <button
              onClick={accept}
              className="w-full py-3 rounded-xl bg-[#16A34A] text-white text-sm font-bold hover:bg-[#15803d] transition-colors"
            >
              I am 18+ and understand
            </button>
            <button
              onClick={decline}
              className="w-full py-2.5 rounded-xl bg-transparent border border-[#1E293B] text-[#94A3B8] text-sm font-medium hover:text-[#F8FAFC] hover:border-[#475569] transition-colors"
            >
              I am under 18 / Exit
            </button>
          </div>

          <p className="text-[10px] text-[#94A3B8]/60 text-center">
            By continuing you confirm you meet the legal age requirement and accept that
            predictions carry risk. Bet responsibly.
          </p>
        </div>
      </div>
    </div>
  );
}
