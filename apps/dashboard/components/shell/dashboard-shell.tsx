import type { ReactNode } from "react";

import { DashboardNavigation } from "@/components/shell/dashboard-navigation";

export function DashboardShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen text-slate-950">
      <a href="#dashboard-main" className="skip-link">
        Skip to main content
      </a>

      <header className="pointer-events-none fixed inset-x-0 top-0 z-50 px-3 pt-3 sm:px-5 sm:pt-4">
        <div className="mx-auto flex w-full max-w-[1500px] items-center justify-between gap-3">
          <div className="glass-floating pointer-events-auto flex min-h-12 items-center gap-3 rounded-full px-4 py-2.5 shadow-[0_16px_40px_rgba(15,23,42,0.14)]">
            <div
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-950 text-xs font-black tracking-tight text-white"
              aria-hidden="true"
            >
              FE
            </div>
            <div className="min-w-0">
              <div className="truncate text-xs font-black uppercase tracking-[0.14em] text-slate-950">
                Fin Engine
              </div>
              <div className="hidden text-[11px] font-medium text-slate-600 sm:block">
                Vehicle value explorer
              </div>
            </div>
          </div>

          <div className="pointer-events-auto hidden md:block">
            <DashboardNavigation variant="desktop" />
          </div>

          <div
            className="glass-floating pointer-events-auto inline-flex min-h-11 shrink-0 items-center rounded-full px-3.5 py-2 text-xs font-black text-blue-950 shadow-[0_12px_32px_rgba(15,23,42,0.10)]"
            aria-label="Proof of concept environment"
          >
            <span className="mr-2 h-2 w-2 rounded-full bg-blue-700" aria-hidden="true" />
            POC
          </div>
        </div>
      </header>

      <main
        id="dashboard-main"
        className="min-w-0 px-4 pb-28 pt-24 sm:px-6 md:pb-10 md:pt-28 lg:px-8 xl:px-10"
        tabIndex={-1}
      >
        <div className="data-grid mx-auto min-h-[calc(100vh-7rem)] w-full max-w-[1420px] rounded-[2rem] px-0 py-4 sm:py-6 lg:py-8">
          <div className="mx-auto w-full max-w-[1360px]">{children}</div>
        </div>
      </main>

      <div className="pointer-events-none fixed inset-x-0 bottom-0 z-50 px-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] md:hidden">
        <div className="pointer-events-auto mx-auto max-w-md">
          <DashboardNavigation variant="mobile" />
        </div>
      </div>
    </div>
  );
}
