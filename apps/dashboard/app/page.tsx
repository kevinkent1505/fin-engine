import Link from "next/link";

import { MetricCard } from "@/components/ui/metric-card";
import { SourceBadge } from "@/components/ui/source-badge";
import { RegionalMarketChart } from "@/features/market-intelligence/regional-market-chart";
import { ValueComparisonChart } from "@/features/vehicle-intelligence/value-comparison-chart";
import { getDashboardData } from "@/lib/data";
import { formatPercent, formatRupiahCompact } from "@/lib/format";

export default async function OverviewPage() {
  const data = await getDashboardData();
  const snapshot = data.snapshot;

  const asking = snapshot.values.find((item) => item.kind === "listing")!;
  const njkb = snapshot.values.find((item) => item.kind === "njkb")!;
  const auction = snapshot.values.find((item) => item.kind === "auction_limit")!;

  const metrics = [
    {
      label: "Indicative asking median",
      value: formatRupiahCompact(asking.value),
      helper: `${snapshot.sampleSize} illustrative marketplace observations`,
    },
    {
      label: "Official NJKB",
      value: formatRupiahCompact(njkb.value),
      helper: "Permendagri No. 7 Tahun 2025",
      tone: "positive" as const,
    },
    {
      label: "Market / NJKB",
      value: `${(asking.value / njkb.value).toFixed(2)}×`,
      helper: `${formatPercent((asking.value - njkb.value) / njkb.value)} above NJKB reference`,
    },
    {
      label: "Auction / asking",
      value: `${(auction.value / asking.value).toFixed(2)}×`,
      helper: "Illustrative downside signal for POC",
      tone: "warning" as const,
    },
  ];

  return (
    <div className="space-y-6 sm:space-y-7">
      <section className="flex flex-col justify-between gap-5 xl:flex-row xl:items-end">
        <div className="min-w-0">
          <div className="text-xs font-bold uppercase tracking-[0.18em] text-blue-800">
            Executive overview
          </div>
          <h1 className="mt-2 max-w-3xl text-2xl font-semibold tracking-tight text-slate-950 sm:text-3xl md:text-4xl">
            Vehicle collateral intelligence from traceable public and market signals.
          </h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-700 md:text-base">
            This POC demonstrates how Fin Engine can combine official references, market observations and auction signals without treating them as the same kind of value.
          </p>
        </div>

        <Link
          href="/vehicle"
          className="inline-flex min-h-11 w-full items-center justify-center rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-slate-950/10 transition hover:bg-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-700 focus-visible:ring-offset-2 sm:w-fit"
        >
          Open vehicle intelligence
          <span aria-hidden="true" className="ml-2">→</span>
        </Link>
      </section>

      <aside className="rounded-2xl border border-amber-300/80 bg-amber-50/90 px-4 py-3 text-sm leading-6 text-amber-950 shadow-sm backdrop-blur-md" aria-label="POC data mode notice">
        <strong>POC data mode:</strong> BPS regional vehicle-stock and Kemendagri NJKB values are official public references. Marketplace asking-price and auction figures on this screen are illustrative placeholders until the authorized ingestion jobs are connected to the dashboard query layer.
      </aside>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Executive metrics">
        {metrics.map((metric) => (
          <MetricCard key={metric.label} metric={metric} />
        ))}
      </section>

      <section className="grid gap-5 xl:grid-cols-[1.12fr_0.88fr]" aria-label="Vehicle signal summary">
        <ValueComparisonChart values={snapshot.values} />

        <article className="glass-panel min-w-0 rounded-2xl p-4 sm:p-5">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-sm font-semibold text-slate-950">POC vehicle</h2>
              <p className="mt-1 text-xs text-slate-600">Current business-demo selection</p>
            </div>
            <span className="inline-flex min-h-8 w-fit items-center rounded-full border border-slate-300/80 bg-white/70 px-3 py-1 text-xs font-semibold text-slate-700">
              {snapshot.region}
            </span>
          </div>

          <div className="mt-6 border-b border-slate-200/80 pb-6">
            <div className="break-words text-2xl font-semibold tracking-tight text-slate-950 sm:text-3xl">
              {snapshot.make} {snapshot.model}
            </div>
            <div className="mt-2 text-sm text-slate-600">
              {snapshot.variant} · {snapshot.year}
            </div>
          </div>

          <dl className="mt-5 grid grid-cols-1 gap-5 text-sm xs:grid-cols-2 sm:grid-cols-2">
            <div>
              <dt className="text-slate-600">Observed range</dt>
              <dd className="mt-1 font-semibold text-slate-950">
                {formatRupiahCompact(snapshot.observedRange[0])}–{formatRupiahCompact(snapshot.observedRange[1])}
              </dd>
            </div>
            <div>
              <dt className="text-slate-600">Comparable count</dt>
              <dd className="mt-1 font-semibold text-slate-950">{snapshot.sampleSize}</dd>
            </div>
            <div>
              <dt className="text-slate-600">Official reference</dt>
              <dd className="mt-1 font-semibold text-slate-950">NJKB 2025</dd>
            </div>
            <div>
              <dt className="text-slate-600">Refresh status</dt>
              <dd className="mt-1 font-semibold text-slate-950">{snapshot.lastRefresh}</dd>
            </div>
          </dl>
        </article>
      </section>

      <section className="grid gap-5 xl:grid-cols-[1.18fr_0.82fr]" aria-label="Regional market and provenance">
        <RegionalMarketChart data={data.regionalMarket} />

        <article className="glass-panel min-w-0 rounded-2xl p-4 sm:p-5">
          <div>
            <h2 className="text-sm font-semibold text-slate-950">Data provenance</h2>
            <p className="mt-1 text-xs leading-5 text-slate-600">
              Business users can see which signals are official and which are still POC placeholders.
            </p>
          </div>

          <div className="mt-5 space-y-3">
            {data.sources.map((source) => (
              <div key={source.id} className="glass-subpanel rounded-xl p-4">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div className="min-w-0">
                    <div className="break-words text-sm font-semibold text-slate-950">{source.name}</div>
                    <div className="mt-1 text-xs text-slate-600">{source.type}</div>
                  </div>
                  <div className="shrink-0">
                    <SourceBadge confidence={source.confidence} />
                  </div>
                </div>
                <p className="mt-3 text-xs leading-5 text-slate-700">{source.note}</p>
              </div>
            ))}
          </div>
        </article>
      </section>
    </div>
  );
}
