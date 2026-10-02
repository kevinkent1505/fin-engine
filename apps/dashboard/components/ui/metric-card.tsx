import type { Metric } from "@/lib/types";

const toneClass = {
  default: "text-slate-950",
  positive: "text-emerald-800",
  warning: "text-amber-800",
};

export function MetricCard({ metric }: { metric: Metric }) {
  const tone = metric.tone ?? "default";

  return (
    <article
      className="glass-panel min-w-0 rounded-2xl p-4 sm:p-5"
      aria-label={`${metric.label}: ${metric.value}`}
    >
      <div className="text-[11px] font-bold uppercase tracking-[0.14em] text-slate-600 sm:text-xs">
        {metric.label}
      </div>
      <div
        className={`mt-3 break-words text-2xl font-semibold tracking-tight sm:text-3xl ${toneClass[tone]}`}
      >
        {metric.value}
      </div>
      {metric.helper ? (
        <p className="mt-2 text-sm leading-5 text-slate-600">{metric.helper}</p>
      ) : null}
    </article>
  );
}
