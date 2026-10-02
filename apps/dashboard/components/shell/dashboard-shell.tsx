import type { ReactNode } from "react";

import { DashboardNavigation } from "@/components/shell/dashboard-navigation";

export function DashboardShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen text-slate-950">
      <a href="#dashboard-main" className="skip-link">
        Skip to main content
      </a>

      <div className="mx-auto grid min-h-screen w-full max-w-[1680px] lg:grid-cols-[260px_minmax(0,1fr)]">
        <aside className="hidden border-r border-white/10 bg-slate-950/[0.92] px-5 py-7 text-white shadow-2xl backdrop-blur-2xl lg:sticky lg:top-0 lg:block lg:h-screen">
          <div className="mb-9">
            <div className="text-xs font-bold uppercase tracking-[0.2em] text-sky-300">
              Riil
            </div>
            <div className="mt-2 text-xl font-semibold tracking-tight">Fin Engine</div>
            <div className="mt-1 text-sm leading-5 text-slate-300">Collateral Intelligence POC</div>
          </div>

          <DashboardNavigation variant="desktop" />

          <div className="mt-10 rounded-2xl border border-white/20 bg-white/10 p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.12)] backdrop-blur-xl">
            <div className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-300">
              Data mode
            </div>
            <div className="mt-2 text-sm font-semibold text-white">POC / reference mode</div>
            <div className="mt-2 text-xs leading-5 text-slate-300">
              Official public references are separated from illustrative market signals.
            </div>
          </div>
        </aside>

        <main id="dashboard-main" className="min-w-0" tabIndex={-1}>
          <header className="glass-header sticky top-0 z-30 px-4 py-3 sm:px-6 md:px-8 lg:px-10">
            <div className="flex items-center justify-between gap-4">
              <div className="min-w-0">
                <div className="truncate text-xs font-bold uppercase tracking-[0.16em] text-slate-700 lg:hidden">
                  Riil · Fin Engine
                </div>
                <div className="hidden text-sm font-semibold text-slate-700 lg:block">
                  Business dashboard proof of concept
                </div>
              </div>
              <div
                className="inline-flex min-h-9 shrink-0 items-center rounded-full border border-blue-200/80 bg-blue-50/90 px-3 py-1.5 text-xs font-bold text-blue-800 shadow-sm"
                aria-label="Proof of concept environment"
              >
                POC
              </div>
            </div>
            <div className="mt-3 lg:hidden">
              <DashboardNavigation variant="mobile" />
            </div>
          </header>

          <div className="data-grid min-h-[calc(100vh-65px)] px-4 py-6 sm:px-6 md:px-8 lg:px-10 lg:py-9">
            <div className="mx-auto w-full max-w-[1360px]">{children}</div>
          </div>
        </main>
      </div>
    </div>
  );
}
