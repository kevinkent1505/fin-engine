import type { AnalysisStatus as AnalysisStatusModel } from "@/lib/types";

const stateClass: Record<AnalysisStatusModel["state"], string> = {
  database:
    "border-emerald-400 bg-emerald-50 text-emerald-950",
  development:
    "border-blue-400 bg-blue-50 text-blue-950",
  fallback:
    "border-amber-500 bg-amber-50 text-amber-950",
};

const dotClass: Record<AnalysisStatusModel["state"], string> = {
  database: "bg-emerald-700",
  development: "bg-blue-700",
  fallback: "bg-amber-700",
};

const connectionLabel: Record<AnalysisStatusModel["state"], string> = {
  database: "Connected",
  development: "Demo mode",
  fallback: "Fallback mode",
};

const sourceLabel: Record<AnalysisStatusModel["state"], string> = {
  database: "Marketplace listings",
  development: "Demo comparison data",
  fallback: "Default demo data",
};

export function AnalysisStatus({ status }: { status: AnalysisStatusModel }) {
  return (
    <section
      className={`rounded-2xl border px-4 py-3 shadow-sm ${stateClass[status.state]}`}
      aria-label={`Dashboard data status: ${status.label}`}
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex min-w-0 items-start gap-3">
          <span
            className={`mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full ${dotClass[status.state]}`}
            aria-hidden="true"
          />
          <div className="min-w-0">
            <div className="text-xs font-black uppercase tracking-[0.12em]">
              {status.label}
            </div>
            <p className="mt-1 text-sm font-semibold leading-5">
              {status.detail}
            </p>
          </div>
        </div>

        <div className="flex shrink-0 flex-wrap gap-2 sm:justify-end">
          <span className="inline-flex min-h-8 items-center rounded-full border border-current/25 bg-white/80 px-3 py-1 text-[11px] font-black uppercase tracking-[0.08em]">
            {connectionLabel[status.state]}
          </span>
          <span className="inline-flex min-h-8 items-center rounded-full border border-current/25 bg-white/80 px-3 py-1 text-[11px] font-black uppercase tracking-[0.08em]">
            {sourceLabel[status.state]}
          </span>
        </div>
      </div>
    </section>
  );
}
