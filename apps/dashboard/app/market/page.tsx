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
    <div className="space-y-7">
      <section>
        <div className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-700">
          Market intelligence
        </div>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950 md:text-4xl">
          Regional market context for collateral decisions.
        </h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600 md:text-base">
          The POC combines official vehicle-stock statistics with placeholder price signals to show how Fin Engine can move from single-asset valuation toward portfolio and regional intelligence.
        </p>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
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

        <div className="rounded-2xl border border-slate-200 bg-white p-5">
          <h2 className="text-sm font-semibold text-slate-900">Regional comparison</h2>
          <p className="mt-1 text-xs leading-5 text-slate-500">
            Asking-price medians are illustrative in the current POC. Passenger-car counts are official BPS references.
          </p>

          <div className="mt-5 overflow-hidden rounded-xl border border-slate-100">
            <table className="w-full border-collapse text-left text-xs">
              <thead className="bg-slate-50 text-slate-500">
                <tr>
                  <th className="px-3 py-3 font-semibold">Province</th>
                  <th className="px-3 py-3 text-right font-semibold">Passenger cars</th>
                  <th className="px-3 py-3 text-right font-semibold">POC asking</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.regionalMarket.map((item) => (
                  <tr key={item.region} className="bg-white">
                    <td className="px-3 py-3 font-medium text-slate-900">{item.region}</td>
                    <td className="px-3 py-3 text-right text-slate-600">
                      {new Intl.NumberFormat("en").format(item.passengerCars)}
                    </td>
                    <td className="px-3 py-3 text-right font-medium text-slate-900">
                      {item.marketMedian ? formatRupiahCompact(item.marketMedian) : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-5">
        <div className="grid gap-6 md:grid-cols-3">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">What this can become</div>
            <div className="mt-2 text-lg font-semibold text-slate-950">Market depth</div>
            <p className="mt-2 text-sm leading-6 text-slate-500">
              Combine vehicle population, active listings and observed turnover to estimate how deep each regional market is.
            </p>
          </div>
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">What this can become</div>
            <div className="mt-2 text-lg font-semibold text-slate-950">Liquidity signal</div>
            <p className="mt-2 text-sm leading-6 text-slate-500">
              Use repeated listing observations, disappearance and price reductions to build an evidence-based liquidity feature.
            </p>
          </div>
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">What this can become</div>
            <div className="mt-2 text-lg font-semibold text-slate-950">Portfolio monitoring</div>
            <p className="mt-2 text-sm leading-6 text-slate-500">
              Track collateral value and downside changes across model, year and geography instead of reviewing one asset at a time.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
