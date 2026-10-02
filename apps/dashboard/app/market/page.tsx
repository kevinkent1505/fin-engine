import { MetricCard } from "@/components/ui/metric-card";
import { RegionalMarketChart } from "@/features/market-intelligence/regional-market-chart";
import { getDashboardData } from "@/lib/data";
import { formatNumberCompact, formatRupiahCompact } from "@/lib/format";

export default async function MarketIntelligencePage() {
  const data = await getDashboardData();
  const totalPassengerCars = data.regionalMarket.reduce(
    (sum, item) => sum + item.passengerCars,
    0,
  );
  const largest = [...data.regionalMarket].sort(
    (a, b) => b.passengerCars - a.passengerCars,
  )[0];
  const highestIllustrativeMarket = [...data.regionalMarket]
    .filter((item) => item.marketMedian)
    .sort((a, b) => (b.marketMedian ?? 0) - (a.marketMedian ?? 0))[0];

  return (
    <div className="space-y-6 sm:space-y-7">
      <section>
        <div className="text-xs font-bold uppercase tracking-[0.18em] text-blue-800">
          Market intelligence
        </div>
        <h1 className="mt-2 max-w-4xl text-2xl font-semibold tracking-tight text-slate-950 sm:text-3xl md:text-4xl">
          Regional market context for collateral decisions.
        </h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-700 md:text-base">
          The POC combines official vehicle-stock statistics with placeholder price signals to show how Fin Engine can move from single-asset valuation toward portfolio and regional intelligence.
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
            label: "POC regional coverage",
            value: String(data.regionalMarket.length),
            helper: "Selected provinces for the first dashboard slice",
          }}
        />
        <MetricCard
          metric={{
            label: "Highest illustrative asking median",
            value: formatRupiahCompact(highestIllustrativeMarket.marketMedian ?? 0),
            helper: highestIllustrativeMarket.region,
            tone: "warning",
          }}
        />
      </section>

      <section className="grid gap-5 xl:grid-cols-[1.15fr_0.85fr]">
        <RegionalMarketChart data={data.regionalMarket} />

        <article className="glass-panel min-w-0 rounded-2xl p-4 sm:p-5">
          <h2 className="text-sm font-semibold text-slate-950">Regional comparison</h2>
          <p className="mt-1 text-xs leading-5 text-slate-600">
            Asking-price medians are illustrative in the current POC. Passenger-car counts are official BPS references.
          </p>

          <div className="mt-5 overflow-x-auto rounded-xl border border-white/70 bg-white/55 backdrop-blur-md" tabIndex={0} aria-label="Scrollable regional comparison table">
            <table className="w-full min-w-[34rem] border-collapse text-left text-xs">
              <caption className="sr-only">Regional passenger-car stock and illustrative asking-price comparison</caption>
              <thead className="bg-slate-100/80 text-slate-700">
                <tr>
                  <th scope="col" className="px-3 py-3 font-bold">Province</th>
                  <th scope="col" className="px-3 py-3 text-right font-bold">Passenger cars</th>
                  <th scope="col" className="px-3 py-3 text-right font-bold">POC asking</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200/80">
                {data.regionalMarket.map((item) => (
                  <tr key={item.region} className="bg-white/45">
                    <th scope="row" className="px-3 py-3 font-semibold text-slate-950">{item.region}</th>
                    <td className="px-3 py-3 text-right text-slate-700">
                      {new Intl.NumberFormat("en").format(item.passengerCars)}
                    </td>
                    <td className="px-3 py-3 text-right font-semibold text-slate-950">
                      {item.marketMedian ? formatRupiahCompact(item.marketMedian) : "—"}
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
            <div className="text-xs font-bold uppercase tracking-[0.14em] text-slate-600">What this can become</div>
            <div className="mt-2 text-lg font-semibold text-slate-950">Market depth</div>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Combine vehicle population, active listings and observed turnover to estimate how deep each regional market is.
            </p>
          </article>
          <article>
            <div className="text-xs font-bold uppercase tracking-[0.14em] text-slate-600">What this can become</div>
            <div className="mt-2 text-lg font-semibold text-slate-950">Liquidity signal</div>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Use repeated listing observations, disappearance and price reductions to build an evidence-based liquidity feature.
            </p>
          </article>
          <article>
            <div className="text-xs font-bold uppercase tracking-[0.14em] text-slate-600">What this can become</div>
            <div className="mt-2 text-lg font-semibold text-slate-950">Portfolio monitoring</div>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Track collateral value and downside changes across model, year and geography instead of reviewing one asset at a time.
            </p>
          </article>
        </div>
      </section>
    </div>
  );
}
