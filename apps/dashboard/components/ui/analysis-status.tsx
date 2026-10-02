import type { AnalysisStatus as AnalysisStatusModel } from "@/lib/types";

const stateClass: Record<AnalysisStatusModel["state"], string> = {
  database:
    "border-emerald-300/80 bg-emerald-50/90 text-emerald-950",
  development:
    "border-blue-300/80 bg-blue-50/90 text-blue-950",
  fallback:
    "border-amber-300/80 bg-amber-50/95 text-amber-950",
};

const dotClass: Record<AnalysisStatusModel["state"], string> = {
  database: "bg-emerald-700",
  development: "bg-blue-700",
  fallback: "bg-amber-700",
};

export function AnalysisStatus({ status }: { status: AnalysisStatusModel }) {
  return (
    <section
      className={`rounded-2xl border px-4 py-3 shadow-sm ${stateClass[status.state]}`}
      aria-label={`Dashboard data status: ${status.label}`}
    >
      <div className="flex items-start gap-3">
        <span
          className={`mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full ${dotClass[status.state]}`}
          aria-hidden="true"
        />
        <div className="min-w-0">
          <div className="text-xs font-black uppercase tracking-[0.12em]">
            {status.label}
          </div>
          <p className="mt-1 text-sm font-medium leading-5 opacity-90">
            {status.detail}
          </p>
          {status.method ? (
            <div className="mt-2 text-[11px] font-bold uppercase tracking-[0.1em] opacity-75">
              Method: {status.method}
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}
