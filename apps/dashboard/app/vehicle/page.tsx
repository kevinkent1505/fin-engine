import { AnalysisStatus } from "@/components/ui/analysis-status";
import { MetricCard } from "@/components/ui/metric-card";
import { SourceBadge } from "@/components/ui/source-badge";
import { PriceHistoryChart } from "@/features/vehicle-intelligence/price-history-chart";
import { ValueComparisonChart } from "@/features/vehicle-intelligence/value-comparison-chart";
import { getDashboardData } from "@/lib/data";
import { formatPercent, formatRupiahCompact } from "@/lib/format";

export default async function VehicleIntelligencePage() {
  const data = await getDashboardData();
  const snapshot = data.snapshot;
  const asking = snapshot.values.find((item) => item.kind === "listing")!;
  const njkb = snapshot.values.find((item) => item.kind === "njkb")!;
  const auction = snapshot.values.find((item) => item.kind === "auction_limit")!;

  const askingHelper =
    data.analysis.state === "database"
      ? "Latest persisted marketplace observations via Python analysis engine"
      : data.analysis.state === "development"
        ? "Python analysis engine using development comparable CSV"
        : "Illustrative fallback because analysis did not return comparables";

  return (
    <div className="space-y-6 sm:space-y-7">
      <section>
        <div className="text-xs font-bold uppercase tracking-[0.18em] text-blue-900">
          Vehicle intelligence
        </div>
        <div className="mt-2 flex flex-col justify-between gap-4 xl:flex-row xl:items-end">
          <div className="min-w-0">
            <h1 className="break-words text-2xl font-semibold tracking-tight text-slate-950 sm:text-3xl md:text-4xl">
              {snapshot.make} {snapshot.model} {snapshot.year}
            </h1>
            <p className="mt-2 text-sm text-slate-700">
              {snapshot.variant} · {snapshot.region}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <span className="inline-flex min-h-9 items-center rounded-full border border-slate-400/70 bg-white/90 px-3 py-1.5 text-xs font-bold text-slate-900 shadow-sm backdrop-blur-md">
              {snapshot.sampleSize} comparables
            </span>
            <span className="inline-flex min-h-9 items-center rounded-full border border-slate-400/70 bg-white/90 px-3 py-1.5 text-xs font-bold text-slate-900 shadow-sm backdrop-blur-md">
              {data.analysis.state === "database" ? "Observed data" : "POC mode"}
            </span>
          </div>
        </div>
      </section>

      <AnalysisStatus status={data.analysis} />

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Vehicle intelligence metrics">
        <MetricCard
          metric={{
            label: "Indicative asking median",
            value: formatRupiahCompact(asking.value),
            helper: askingHelper,
          }}
        />
        <MetricCard
          metric={{
            label: "Official NJKB",
            value: formatRupiahCompact(njkb.value),
            helper: "Kemendagri 2025 reference",
            tone: "positive",
          }}
        />
        <MetricCard
          metric={{
            label: "Market premium to NJKB",
            value: formatPercent((asking.value - njkb.value) / njkb.value),
            helper: "Relationship between the asking-value signal and official reference",
          }}
        />
        <MetricCard
          metric={{
            label: "Downside gap",
            value: formatPercent((auction.value - asking.value) / asking.value),
            helper: "Auction signal remains illustrative in this POC",
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
          <h2 className="text-sm font-semibold text-slate-950">Collateral signal summary</h2>
          <div className="mt-5 space-y-5">
            <div>
              <div className="text-xs font-bold uppercase tracking-[0.14em] text-slate-700">Official reference</div>
              <div className="mt-1 text-xl font-semibold text-slate-950">{formatRupiahCompact(njkb.value)}</div>
              <p className="mt-1 text-xs leading-5 text-slate-700">
                Official NJKB benchmark. It is not itself a retail market price.
              </p>
            </div>
            <div>
              <div className="text-xs font-bold uppercase tracking-[0.14em] text-slate-700">Indicative market signal</div>
              <div className="mt-1 text-xl font-semibold text-slate-950">{formatRupiahCompact(asking.value)}</div>
              <p className="mt-1 text-xs leading-5 text-slate-700">
                {askingHelper}.
              </p>
            </div>
            <div>
              <div className="text-xs font-bold uppercase tracking-[0.14em] text-slate-700">Downside signal</div>
              <div className="mt-1 text-xl font-semibold text-slate-950">{formatRupiahCompact(auction.value)}</div>
              <p className="mt-1 text-xs leading-5 text-slate-700">
                Auction-limit style reference. It should not be represented as a confirmed transaction value.
              </p>
            </div>
          </div>
        </article>

        <article className="glass-panel rounded-2xl p-4 sm:p-5">
          <h2 className="text-sm font-semibold text-slate-950">Evidence behind this screen</h2>
          <p className="mt-1 text-xs leading-5 text-slate-700">
            Provenance remains visible so a business user can distinguish official evidence, observed analysis-engine output and illustrative POC content.
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