import Link from "next/link";

import { AnalysisStatus } from "@/components/ui/analysis-status";
import { MetricCard } from "@/components/ui/metric-card";
import { SourceBadge } from "@/components/ui/source-badge";
import { VehicleChooser } from "@/components/ui/vehicle-chooser";
import { RegionalMarketChart } from "@/features/market-intelligence/regional-market-chart";
import { ValueComparisonChart } from "@/features/vehicle-intelligence/value-comparison-chart";
import {
  getDashboardData,
  getVehicleCatalog,
  resolveVehicleSelection,
} from "@/lib/data";
import { formatPercent, formatRupiahCompact } from "@/lib/format";

function vehicleQuery(vehicle: {
  make: string;
  model: string;
  year: number;
  region: string;
}) {
  return new URLSearchParams({
    make: vehicle.make,
    model: vehicle.model,
    year: String(vehicle.year),
    region: vehicle.region,
  }).toString();
}

export default async function OverviewPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const query = await searchParams;
  const catalog = await getVehicleCatalog();
  const selected = resolveVehicleSelection(
    {
      make: typeof query.make === "string" ? query.make : undefined,
      model: typeof query.model === "string" ? query.model : undefined,
      year: typeof query.year === "string" ? query.year : undefined,
      region: typeof query.region === "string" ? query.region : undefined,
    },
    catalog.options,
  );
  const data = await getDashboardData(selected);
  const snapshot = data.snapshot;

  const asking = snapshot.values.find((item) => item.kind === "listing")!;
  const njkb = snapshot.values.find((item) => item.kind === "njkb");
  const auction = snapshot.values.find((item) => item.kind === "auction_limit");

  const askingHelper =
    data.analysis.state === "database"
      ? `Based on ${snapshot.sampleSize} matching marketplace listings`
      : data.analysis.state === "development"
        ? `Based on ${snapshot.sampleSize} matching demo comparison rows`
        : "Illustrative default demo data";

  const metrics = [
    {
      label: "Estimated asking price",
      value: formatRupiahCompact(asking.value),
      helper: `${askingHelper}. This is an asking-price estimate, not a confirmed sale price.`,
    },
    {
      label: "Official NJKB reference",
      value: njkb ? formatRupiahCompact(njkb.value) : "Not matched yet",
      helper: njkb
        ? "Government reference value for the demo vehicle configuration"
        : "No official NJKB value has been safely matched to this vehicle yet.",
      tone: "positive" as const,
    },
    {
      label: "Difference from NJKB",
      value: njkb
        ? `${formatPercent((asking.value - njkb.value) / njkb.value)}`
        : "Not available",
      helper: njkb
        ? "How much higher or lower the estimated asking price is than the official reference"
        : "Shown only when the official reference matches the selected vehicle.",
    },
    {
      label: "Auction / downside reference",
      value: auction
        ? `${(auction.value / asking.value).toFixed(2)}×`
        : "Not available",
      helper: auction
        ? "Illustrative lower-value reference for the default demo vehicle"
        : "A matched auction reference is not available for this vehicle yet.",
      tone: "warning" as const,
    },
  ];

  const actualSelection = {
    make: snapshot.make,
    model: snapshot.model,
    year: snapshot.year,
    region: snapshot.region,
  };

  return (
    <div className="space-y-6 sm:space-y-7">
      <section className="flex flex-col justify-between gap-5 xl:flex-row xl:items-end">
        <div className="min-w-0">
          <div className="text-xs font-bold uppercase tracking-[0.18em] text-blue-900">
            Overview
          </div>
          <h1 className="mt-2 max-w-3xl text-2xl font-semibold tracking-tight text-slate-950 sm:text-3xl md:text-4xl">
            Understand what a vehicle may be worth and where the number comes from.
          </h1>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-700 md:text-base">
            Choose a vehicle below. The dashboard compares available market listings and clearly separates real observations, official references and demo-only information.
          </p>
        </div>

        <Link
          href={`/vehicle?${vehicleQuery(actualSelection)}`}
          className="action-primary w-full sm:w-fit"
        >
          See vehicle details
          <span aria-hidden="true" className="ml-2">→</span>
        </Link>
      </section>

      <VehicleChooser catalog={catalog} selected={selected} />

      <AnalysisStatus status={data.analysis} />

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Key vehicle numbers">
        {metrics.map((metric) => (
          <MetricCard key={metric.label} metric={metric} />
        ))}
      </section>

      <section className="grid gap-5 xl:grid-cols-[1.12fr_0.88fr]" aria-label="Vehicle value summary">
        <ValueComparisonChart values={snapshot.values} />

        <article className="glass-panel min-w-0 rounded-2xl p-4 sm:p-5">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-sm font-semibold text-slate-950">Selected vehicle</h2>
              <p className="mt-1 text-xs text-slate-600">The vehicle currently used for the numbers on this page</p>
            </div>
            <span className="inline-flex min-h-8 w-fit items-center rounded-full border border-slate-400/70 bg-white/90 px-3 py-1 text-xs font-bold text-slate-900">
              {snapshot.region}
            </span>
          </div>

          <div className="mt-6 border-b border-slate-200/80 pb-6">
            <div className="break-words text-2xl font-semibold tracking-tight text-slate-950 sm:text-3xl">
              {snapshot.make} {snapshot.model}
            </div>
            <div className="mt-2 text-sm text-slate-700">
              {snapshot.year} · {snapshot.variant}
            </div>
          </div>

          <dl className="mt-5 grid grid-cols-1 gap-5 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-slate-600">Typical listing range</dt>
              <dd className="mt-1 font-semibold text-slate-950">
                {formatRupiahCompact(snapshot.observedRange[0])}–{formatRupiahCompact(snapshot.observedRange[1])}
              </dd>
            </div>
            <div>
              <dt className="text-slate-600">Listings compared</dt>
              <dd className="mt-1 font-semibold text-slate-950">{snapshot.sampleSize}</dd>
            </div>
            <div>
              <dt className="text-slate-600">Official reference</dt>
              <dd className="mt-1 font-semibold text-slate-950">
                {njkb ? "NJKB matched" : "Not matched yet"}
              </dd>
            </div>
            <div>
              <dt className="text-slate-600">Where the estimate came from</dt>
              <dd className="mt-1 font-semibold text-slate-950">{snapshot.lastRefresh}</dd>
            </div>
          </dl>
        </article>
      </section>

      <section className="grid gap-5 xl:grid-cols-[1.18fr_0.82fr]" aria-label="Regional market and data sources">
        <RegionalMarketChart data={data.regionalMarket} />

        <article className="glass-panel min-w-0 rounded-2xl p-4 sm:p-5">
          <div>
            <h2 className="text-sm font-semibold text-slate-950">Where the data comes from</h2>
            <p className="mt-1 text-xs leading-5 text-slate-700">
              Each source is labelled so you can tell the difference between government data, marketplace observations and demo-only information.
            </p>
          </div>

          <div className="mt-5 space-y-3">
            {data.sources.map((source) => (
              <div key={source.id} className="glass-subpanel rounded-xl p-4">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div className="min-w-0">
                    <div className="break-words text-sm font-semibold text-slate-950">{source.name}</div>
                    <div className="mt-1 text-xs text-slate-700">{source.type}</div>
                  </div>
                  <div className="shrink-0">
                    <SourceBadge confidence={source.confidence} />
                  </div>
                </div>
                <p className="mt-3 text-xs leading-5 text-slate-800">{source.note}</p>
              </div>
            ))}
          </div>
        </article>
      </section>
    </div>
  );
}
