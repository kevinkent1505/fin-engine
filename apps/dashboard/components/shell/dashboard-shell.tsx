import Link from "next/link";
import type { ReactNode } from "react";

const navigation = [
  { href: "/", label: "Overview" },
  { href: "/vehicle", label: "Vehicle Intelligence" },
  { href: "/market", label: "Market Intelligence" },
  { href: "/methodology", label: "Data & Methodology" },
];

export function DashboardShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-950">
      <div className="mx-auto grid min-h-screen max-w-[1600px] lg:grid-cols-[240px_1fr]">
        <aside className="hidden border-r border-slate-200 bg-slate-950 px-5 py-7 text-white lg:block">
          <div className="mb-9">
            <div className="text-xs font-semibold uppercase tracking-[0.2em] text-blue-300">
              Riil
            </div>
            <div className="mt-2 text-xl font-semibold tracking-tight">Fin Engine</div>
            <div className="mt-1 text-sm text-slate-400">Collateral Intelligence POC</div>
          </div>

          <nav className="space-y-1">
            {navigation.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="block rounded-xl px-3 py-2.5 text-sm font-medium text-slate-300 transition hover:bg-white/10 hover:text-white"
              >
                {item.label}
              </Link>
            ))}
          </nav>

          <div className="mt-10 rounded-2xl border border-white/10 bg-white/5 p-4">
            <div className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">
              Data mode
            </div>
            <div className="mt-2 text-sm font-semibold text-white">POC / reference mode</div>
            <div className="mt-2 text-xs leading-5 text-slate-400">
              Official public references are separated from illustrative market signals.
            </div>
          </div>
        </aside>

        <main className="min-w-0">
          <header className="border-b border-slate-200 bg-white/90 px-5 py-4 backdrop-blur md:px-8 lg:px-10">
            <div className="flex items-center justify-between gap-4">
              <div>
                <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500 lg:hidden">
                  Riil · Fin Engine
                </div>
                <div className="hidden text-sm font-medium text-slate-600 lg:block">
                  Business dashboard proof of concept
                </div>
              </div>
              <div className="rounded-full border border-blue-200 bg-blue-50 px-3 py-1.5 text-xs font-semibold text-blue-700">
                POC
              </div>
            </div>
            <nav className="mt-4 flex gap-2 overflow-x-auto lg:hidden">
              {navigation.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="whitespace-nowrap rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600"
                >
                  {item.label}
                </Link>
              ))}
            </nav>
          </header>

          <div className="data-grid min-h-[calc(100vh-65px)] px-5 py-7 md:px-8 lg:px-10 lg:py-9">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
