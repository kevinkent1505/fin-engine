import { AnalysisStatus } from "@/components/ui/analysis-status";
import { MetricCard } from "@/components/ui/metric-card";
import { SourceBadge } from "@/components/ui/source-badge";
import { VehicleChooser } from "@/components/ui/vehicle-chooser";
import { PriceHistoryChart } from "@/features/vehicle-intelligence/price-history-chart";
import { ValueComparisonChart } from "@/features/vehicle-intelligence/value-comparison-chart";
import {
  getDashboardData,
  getVehicleCatalog,
  resolveVehicleSelection,
} from "@/lib/data";
import { formatPercent, formatRupiahCompact } from "@/lib/format";

export default async function VehicleIntelligencePage({
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

  return (
    <div className="space-y-6 sm:space-y-7">
      <section>
        <div className="text-xs font-bold uppercase tracking-[0.18em] text-blue-900">
          Vehicle details
        </div>
        <div className="mt-2 flex flex-col justify-between gap-4 xl:flex-row xl:items-end">
          <div className="min-w-0">
            <h1 className="break-words text-2xl font-semibold tracking-tight text-slate-950 sm:text-3xl md:text-4xl">
              {snapshot.make} {snapshot.model} {snapshot.year}
            </h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-700">
              A simple view of the selected vehicle&apos;s estimated asking price, comparison range and available reference data in {snapshot.region}.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <span className="inline-flex min-h-9 items-center rounded-full border border-slate-400/70 bg-white/90 px-3 py-1.5 text-xs font-bold text-slate-900 shadow-sm backdrop-blur-md">
              {snapshot.sampleSize} listings compared
            </span>
            <span className="inline-flex min-h-9 items-center rounded-full border border-slate-400/70 bg-white/90 px-3 py-1.5 text-xs font-bold text-slate-900 shadow-sm backdrop-blur-md">
              {data.analysis.state === "database" ? "Marketplace data" : "Demo mode"}
            </span>
          </div>
        </div>
      </section>

      <VehicleChooser catalog={catalog} selected={selected} />

      <AnalysisStatus status={data.analysis} />

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Vehicle value metrics">
        <MetricCard
          metric={{
            label: "Estimated asking price",
            value: formatRupiahCompact(asking.value),
            helper: `${askingHelper}. This is not a confirmed sale price.`,
          }}
        />
        <MetricCard
          metric={{
            label: "Official NJKB reference",
            value: njkb ? formatRupiahCompact(njkb.value) : "Not matched yet",
            helper: njkb
              ? "Government reference value matched to the default demo configuration"
              : "No official reference has been safely matched to this selection yet.",
            tone: "positive",
          }}
        />
        <MetricCard
          metric={{
            label: "Difference from NJKB",
            value: njkb
              ? formatPercent((asking.value - njkb.value) / njkb.value)
              : "Not available",
            helper: njkb
              ? "How much higher or lower the estimated asking price is than the official reference"
              : "Shown only when the official reference matches the selected vehicle.",
          }}
        />
        <MetricCard
          metric={{
            label: "Auction / downside reference",
            value: auction
              ? formatPercent((auction.value - asking.value) / asking.value)
              : "Not available",
            helper: auction
              ? "Illustrative lower-value reference for the default demo vehicle"
              : "A matched auction reference is not available for this vehicle yet.",
            tone: "warning",
          }}
        />
      </section>

      <section className="grid gap-5 xl:grid-cols-2" aria-label="Vehicle charts">
        <ValueComparisonChart values={snapshot.values} />
        <PriceHistoryChart data={snapshot.priceHistory} />
      </section>

      <section className="grid gap-5 xl:grid-cols-[0.82fr_1.18fr]">
        <article className="glass-panel rounded-2xl p-4 sm:p-5">
          <h2 className="text-sm font-semibold text-slate-950">What these numbers mean</h2>
          <div className="mt-5 space-y-5">
            <div>
              <div className="text-xs font-bold uppercase tracking-[0.14em] text-slate-700">Estimated asking price</div>
              <div className="mt-1 text-xl font-semibold text-slate-950">{formatRupiahCompact(asking.value)}</div>
              <p className="mt-1 text-xs leading-5 text-slate-700">
                A middle-point estimate from matching listings. Sellers may ask for more or less, and the final sale price can differ.
              </p>
            </div>

            {njkb ? (
              <div>
                <div className="text-xs font-bold uppercase tracking-[0.14em] text-slate-700">Official NJKB reference</div>
                <div className="mt-1 text-xl font-semibold text-slate-950">{formatRupiahCompact(njkb.value)}</div>
                <p className="mt-1 text-xs leading-5 text-slate-700">
                  A government reference value. It is not the same thing as a retail market price.
                </p>
              </div>
            ) : (
              <div className="rounded-xl border border-slate-300 bg-white/70 p-3">
                <div className="text-sm font-semibold text-slate-950">Official reference not matched yet</div>
                <p className="mt-1 text-xs leading-5 text-slate-700">
                  The dashboard will not reuse another vehicle&apos;s NJKB value just to fill this space.
                </p>
              </div>
            )}

            {auction ? (
              <div>
                <div className="text-xs font-bold uppercase tracking-[0.14em] text-slate-700">Auction / downside reference</div>
                <div className="mt-1 text-xl font-semibold text-slate-950">{formatRupiahCompact(auction.value)}</div>
                <p className="mt-1 text-xs leading-5 text-slate-700">
                  An illustrative lower-value reference. It is not a confirmed transaction price.
                </p>
              </div>
            ) : null}
          </div>
        </article>

        <article className="glass-panel rounded-2xl p-4 sm:p-5">
          <h2 className="text-sm font-semibold text-slate-950">Where this information comes from</h2>
          <p className="mt-1 text-xs leading-5 text-slate-700">
            Labels below tell you whether each source is official, based on marketplace observations, or only included for demonstration.
          </p>
          <div className="mt-5 space-y-3">
            {data.sources.slice(0, 5).map((source) => (
              <div key={source.id} className="glass-subpanel flex flex-col gap-3 rounded-xl p-4 sm:flex-row sm:items-start sm:justify-between sm:gap-5">
                <div className="min-w-0">
                  <div className="break-words text-sm font-semibold text-slate-950">{source.name}</div>
                  <div className="mt-1 text-xs leading-5 text-slate-700">{source.note}</div>
                </div>
                <div className="shrink-0">
                  <SourceBadge confidence={source.confidence} />
                </div>
              </div>
            ))}
          </div>
        </article>
      </section>
    </div>
  );
}
