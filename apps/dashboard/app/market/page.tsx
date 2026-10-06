import { MetricCard } from "@/components/ui/metric-card";
import { RegionalMarketChart } from "@/features/market-intelligence/regional-market-chart";
import { requestAnalysisRegionalMarket } from "@/lib/data/analysis";
import { formatNumberCompact } from "@/lib/format";

export default async function MarketIntelligencePage() {
  const result = await requestAnalysisRegionalMarket();

  if (result.status !== "ok") {
    return (
      <div className="glass-panel rounded-2xl p-5">
        <div className="text-xs font-bold uppercase tracking-[0.18em] text-amber-800">
          Official regional data unavailable
        </div>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight text-slate-950 sm:text-3xl">
          The latest persisted BPS vehicle-stock table is not available yet.
        </h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-700">
          {result.detail}
        </p>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-700">
          This page does not substitute demo regional values when the official source is unavailable.
        </p>
      </div>
    );
  }

  const regionalMarket = result.data.regions.map((point) => ({
    region: point.region,
    passengerCars: point.passenger_cars,
  }));
  const totalPassengerCars = regionalMarket.reduce(
    (sum, item) => sum + item.passengerCars,
    0,
  );
  const largest = [...regionalMarket].sort(
    (a, b) => b.passengerCars - a.passengerCars,
  )[0];
  const averagePassengerCars = Math.round(
    totalPassengerCars / regionalMarket.length,
  );

  return (
    <div className="space-y-6 sm:space-y-7">
      <section>
        <div className="text-xs font-bold uppercase tracking-[0.18em] text-blue-900">
          Regional market
        </div>
        <h1 className="mt-2 max-w-4xl text-2xl font-semibold tracking-tight text-slate-950 sm:text-3xl md:text-4xl">
          Official passenger-car population by province.
        </h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-700 md:text-base">
          This page uses the persisted {result.data.year} Badan Pusat Statistik vehicle-stock table. It represents registered vehicle stock, not transaction prices or sales volume.
        </p>
        <p className="mt-2 text-xs text-slate-600">
          Official source snapshot observed at {new Date(result.data.observed_at).toLocaleString("en-SG", { timeZone: "Asia/Singapore" })}.
        </p>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Regional market summary">
        <MetricCard
          metric={{
            label: "Passenger cars",
            value: formatNumberCompact(totalPassengerCars),
            helper: "Total across the official provincial records returned by BPS",
            tone: "positive",
          }}
        />
        <MetricCard
          metric={{
            label: "Largest province",
            value: largest.region,
            helper: `${formatNumberCompact(largest.passengerCars)} passenger cars`,
          }}
        />
        <MetricCard
          metric={{
            label: "Regions reported",
            value: String(regionalMarket.length),
            helper: `Official BPS ${result.data.year} rows currently persisted`,
          }}
        />
        <MetricCard
          metric={{
            label: "Average per region",
            value: formatNumberCompact(averagePassengerCars),
            helper: "Simple average across the official rows shown",
          }}
        />
      </section>

      <section className="grid gap-5 xl:grid-cols-[1.15fr_0.85fr]">
        <RegionalMarketChart data={regionalMarket} />

        <article className="glass-panel min-w-0 rounded-2xl p-4 sm:p-5">
          <h2 className="text-sm font-semibold text-slate-950">Province-by-province comparison</h2>
          <p className="mt-1 text-xs leading-5 text-slate-700">
            These are official public counts of passenger cars from BPS.
          </p>

          <div
            className="mt-5 overflow-x-auto rounded-xl border border-white/80 bg-white/70 backdrop-blur-md"
            tabIndex={0}
            aria-label="Scrollable regional comparison table"
          >
            <table className="w-full min-w-[28rem] border-collapse text-left text-xs">
              <caption className="sr-only">Regional passenger-car counts and share of the returned official dataset</caption>
              <thead className="bg-slate-100/90 text-slate-800">
                <tr>
                  <th scope="col" className="px-3 py-3 font-bold">Province</th>
                  <th scope="col" className="px-3 py-3 text-right font-bold">Passenger cars</th>
                  <th scope="col" className="px-3 py-3 text-right font-bold">Share</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200/90">
                {regionalMarket.map((item) => (
                  <tr key={item.region} className="bg-white/60">
                    <th scope="row" className="px-3 py-3 font-semibold text-slate-950">{item.region}</th>
                    <td className="px-3 py-3 text-right text-slate-800">
                      {new Intl.NumberFormat("en").format(item.passengerCars)}
                    </td>
                    <td className="px-3 py-3 text-right font-semibold text-slate-950">
                      {new Intl.NumberFormat("en", {
                        style: "percent",
                        maximumFractionDigits: 1,
                      }).format(item.passengerCars / totalPassengerCars)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <a
            href={result.data.source_url}
            target="_blank"
            rel="noreferrer"
            className="mt-4 block text-sm font-semibold text-blue-900 underline underline-offset-4"
          >
            Open official BPS source
          </a>
        </article>
      </section>
    </div>
  );
}
