import type { Metric } from "@/lib/types";

const toneClass = {
  default: "text-slate-950",
  positive: "text-emerald-700",
  warning: "text-amber-700",
};

export function MetricCard({ metric }: { metric: Metric }) {
  const tone = metric.tone ?? "default";

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_1px_2px_rgba(15,23,42,0.03)]">
      <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
        {metric.label}
      </div>
      <div className={`mt-3 text-3xl font-semibold tracking-tight ${toneClass[tone]}`}>
        {metric.value}
      </div>
      {metric.helper ? (
        <div className="mt-2 text-sm leading-5 text-slate-500">{metric.helper}</div>
      ) : null}
    </div>
  );
}
