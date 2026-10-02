import { MetricCard } from "@/components/ui/metric-card";
import { RegionalMarketChart } from "@/features/market-intelligence/regional-market-chart";
import { getDashboardData } from "@/lib/data";
import { formatNumberCompact } from "@/lib/format";

export default async function MarketIntelligencePage() {
  const data = await getDashboardData();
  const totalPassengerCars = data.regionalMarket.reduce(
    (sum, item) => sum + item.passengerCars,
    0,
  );
  const largest = [...data.regionalMarket].sort(
    (a, b) => b.passengerCars - a.passengerCars,
  )[0];
  const averagePassengerCars = Math.round(
    totalPassengerCars / data.regionalMarket.length,
  );

  return (
    <div className="space-y-6 sm:space-y-7">
      <section>
        <div className="text-xs font-bold uppercase tracking-[0.18em] text-blue-900">
          Market intelligence
        </div>
        <h1 className="mt-2 max-w-4xl text-2xl font-semibold tracking-tight text-slate-950 sm:text-3xl md:text-4xl">
          Regional market context from public statistics.
        </h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-700 md:text-base">
          This POC keeps the regional page on official BPS vehicle-stock data rather than inventing regional price estimates. Live regional pricing can be added later from analysis-engine marketplace observations.
        </p>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Market intelligence metrics">
        <MetricCard
          metric={{
            label: "Passenger cars in selected provinces",
            value: formatNumberCompact(totalPassengerCars),
            helper: "BPS 2023 public-table subset",
            tone: "positive",
          }}
        />
        <MetricCard
          metric={{
            label: "Largest selected market",
            value: largest.region,
            helper: `${formatNumberCompact(largest.passengerCars)} passenger cars`,
          }}
        />
        <MetricCard
          metric={{
            label: "Regional coverage",
            value: String(data.regionalMarket.length),
            helper: "Selected provinces in the public-data POC slice",
          }}
        />
        <MetricCard
          metric={{
            label: "Average selected market",
            value: formatNumberCompact(averagePassengerCars),
            helper: "Passenger cars per selected province",
          }}
        />
      </section>

      <section className="grid gap-5 xl:grid-cols-[1.15fr_0.85fr]">
        <RegionalMarketChart data={data.regionalMarket} />

        <article className="glass-panel min-w-0 rounded-2xl p-4 sm:p-5">
          <h2 className="text-sm font-semibold text-slate-950">Regional comparison</h2>
          <p className="mt-1 text-xs leading-5 text-slate-700">
            These counts are official public BPS references. No synthetic regional asking prices are shown on this page.
          </p>

          <div
            className="mt-5 overflow-x-auto rounded-xl border border-white/80 bg-white/70 backdrop-blur-md"
            tabIndex={0}
            aria-label="Scrollable regional comparison table"
          >
            <table className="w-full min-w-[28rem] border-collapse text-left text-xs">
              <caption className="sr-only">Regional passenger-car stock and share of the selected POC market</caption>
              <thead className="bg-slate-100/90 text-slate-800">
                <tr>
                  <th scope="col" className="px-3 py-3 font-bold">Province</th>
                  <th scope="col" className="px-3 py-3 text-right font-bold">Passenger cars</th>
                  <th scope="col" className="px-3 py-3 text-right font-bold">Selected share</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200/90">
                {data.regionalMarket.map((item) => (
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
        </article>
      </section>

      <section className="glass-panel rounded-2xl p-4 sm:p-5">
        <div className="grid gap-6 md:grid-cols-3">
          <article>
            <div className="text-xs font-bold uppercase tracking-[0.14em] text-slate-700">What this can become</div>
            <div className="mt-2 text-lg font-semibold text-slate-950">Market depth</div>
            <p className="mt-2 text-sm leading-6 text-slate-700">
              Combine public vehicle population with active marketplace listings and observed turnover to estimate how deep each regional market is.
            </p>
          </article>
          <article>
            <div className="text-xs font-bold uppercase tracking-[0.14em] text-slate-700">What this can become</div>
            <div className="mt-2 text-lg font-semibold text-slate-950">Liquidity signal</div>
            <p className="mt-2 text-sm leading-6 text-slate-700">
              Use repeated listing observations, disappearance and price reductions to build an evidence-based liquidity feature.
            </p>
          </article>
          <article>
            <div className="text-xs font-bold uppercase tracking-[0.14em] text-slate-700">What this can become</div>
            <div className="mt-2 text-lg font-semibold text-slate-950">Portfolio monitoring</div>
            <p className="mt-2 text-sm leading-6 text-slate-700">
              Track collateral value and downside changes across model, year and geography instead of reviewing one asset at a time.
            </p>
          </article>
        </div>
      </section>
    </div>
  );
}