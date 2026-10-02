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
    <div className="space-y-7">
      <section className="flex flex-col justify-between gap-5 xl:flex-row xl:items-end">
        <div>
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-700">
            Executive overview
          </div>
          <h1 className="mt-2 max-w-3xl text-3xl font-semibold tracking-tight text-slate-950 md:text-4xl">
            Vehicle collateral intelligence from traceable public and market signals.
          </h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600 md:text-base">
            This POC demonstrates how Fin Engine can combine official references, market observations and auction signals without treating them as the same kind of value.
          </p>
        </div>

        <Link
          href="/vehicle"
          className="inline-flex w-fit items-center rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-800"
        >
          Open vehicle intelligence →
        </Link>
      </section>

      <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm leading-6 text-amber-900">
        <strong>POC data mode:</strong> BPS regional vehicle-stock and Kemendagri NJKB values are official public references. Marketplace asking-price and auction figures on this screen are illustrative placeholders until the authorized ingestion jobs are connected to the dashboard query layer.
      </div>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => (
          <MetricCard key={metric.label} metric={metric} />
        ))}
      </section>

      <section className="grid gap-5 xl:grid-cols-[1.12fr_0.88fr]">
        <ValueComparisonChart values={snapshot.values} />

        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-sm font-semibold text-slate-900">POC vehicle</h2>
              <p className="mt-1 text-xs text-slate-500">Current business-demo selection</p>
            </div>
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
              {snapshot.region}
            </span>
          </div>

          <div className="mt-7 border-b border-slate-100 pb-6">
            <div className="text-3xl font-semibold tracking-tight text-slate-950">
              {snapshot.make} {snapshot.model}
            </div>
            <div className="mt-2 text-sm text-slate-500">
              {snapshot.variant} · {snapshot.year}
            </div>
          </div>

          <dl className="mt-5 grid grid-cols-2 gap-x-6 gap-y-5 text-sm">
            <div>
              <dt className="text-slate-500">Observed range</dt>
              <dd className="mt-1 font-semibold text-slate-900">
                {formatRupiahCompact(snapshot.observedRange[0])}–{formatRupiahCompact(snapshot.observedRange[1])}
              </dd>
            </div>
            <div>
              <dt className="text-slate-500">Comparable count</dt>
              <dd className="mt-1 font-semibold text-slate-900">{snapshot.sampleSize}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Official reference</dt>
              <dd className="mt-1 font-semibold text-slate-900">NJKB 2025</dd>
            </div>
            <div>
              <dt className="text-slate-500">Refresh status</dt>
              <dd className="mt-1 font-semibold text-slate-900">{snapshot.lastRefresh}</dd>
            </div>
          </dl>
        </div>
      </section>

      <section className="grid gap-5 xl:grid-cols-[1.18fr_0.82fr]">
        <RegionalMarketChart data={data.regionalMarket} />

        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <div>
            <h2 className="text-sm font-semibold text-slate-900">Data provenance</h2>
            <p className="mt-1 text-xs leading-5 text-slate-500">
              Business users can see which signals are official and which are still POC placeholders.
            </p>
          </div>

          <div className="mt-5 space-y-4">
            {data.sources.map((source) => (
              <div key={source.id} className="rounded-xl border border-slate-100 bg-slate-50 p-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="text-sm font-semibold text-slate-900">{source.name}</div>
                    <div className="mt-1 text-xs text-slate-500">{source.type}</div>
                  </div>
                  <SourceBadge confidence={source.confidence} />
                </div>
                <p className="mt-3 text-xs leading-5 text-slate-600">{source.note}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
