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

  return (
    <div className="space-y-7">
      <section>
        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-700">
          Vehicle intelligence
        </div>
        <div className="mt-2 flex flex-col justify-between gap-4 xl:flex-row xl:items-end">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight text-slate-950 md:text-4xl">
              {snapshot.make} {snapshot.model} {snapshot.year}
            </h1>
            <p className="mt-2 text-sm text-slate-500">
              {snapshot.variant} · {snapshot.region}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <span className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600">
              {snapshot.sampleSize} comparables
            </span>
            <span className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600">
              POC selection
            </span>
          </div>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          metric={{
            label: "Indicative asking median",
            value: formatRupiahCompact(asking.value),
            helper: "Illustrative until marketplace observations are live",
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
            helper: "POC analytical relationship",
          }}
        />
        <MetricCard
          metric={{
            label: "Downside gap",
            value: formatPercent((auction.value - asking.value) / asking.value),
            helper: "Illustrative auction vs asking median",
            tone: "warning",
          }}
        />
      </section>

      <section className="grid gap-5 xl:grid-cols-2">
        <ValueComparisonChart values={snapshot.values} />
        <PriceHistoryChart data={snapshot.priceHistory} />
      </section>

      <section className="grid gap-5 xl:grid-cols-[0.82fr_1.18fr]">
        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <h2 className="text-sm font-semibold text-slate-900">Collateral signal summary</h2>
          <div className="mt-5 space-y-5">
            <div>
              <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">Reference floor</div>
              <div className="mt-1 text-xl font-semibold text-slate-950">{formatRupiahCompact(njkb.value)}</div>
              <p className="mt-1 text-xs leading-5 text-slate-500">
                Official NJKB benchmark. It is not itself a retail market price.
              </p>
            </div>
            <div>
              <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">Indicative market signal</div>
              <div className="mt-1 text-xl font-semibold text-slate-950">{formatRupiahCompact(asking.value)}</div>
              <p className="mt-1 text-xs leading-5 text-slate-500">
                Marketplace asking-price median in the POC. Replace with live authorized observations before external decision use.
              </p>
            </div>
            <div>
              <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">Downside signal</div>
              <div className="mt-1 text-xl font-semibold text-slate-950">{formatRupiahCompact(auction.value)}</div>
              <p className="mt-1 text-xs leading-5 text-slate-500">
                Auction-limit style reference. It should not be represented as a confirmed transaction value.
              </p>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <h2 className="text-sm font-semibold text-slate-900">Evidence behind this screen</h2>
          <p className="mt-1 text-xs leading-5 text-slate-500">
            The dashboard keeps provenance visible so a business user can distinguish official evidence from illustrative POC content.
          </p>
          <div className="mt-5 space-y-3">
            {data.sources.slice(0, 4).map((source) => (
              <div key={source.id} className="flex items-start justify-between gap-5 rounded-xl border border-slate-100 bg-slate-50 p-4">
                <div>
                  <div className="text-sm font-semibold text-slate-900">{source.name}</div>
                  <div className="mt-1 text-xs text-slate-500">{source.note}</div>
                </div>
                <SourceBadge confidence={source.confidence} />
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
