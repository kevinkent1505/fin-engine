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
          Market overview
        </div>
        <h1 className="mt-2 max-w-4xl text-2xl font-semibold tracking-tight text-slate-950 sm:text-3xl md:text-4xl">
          See where passenger cars are concentrated across selected provinces.
        </h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-700 md:text-base">
          This page uses official BPS vehicle-count data. It shows the size of the passenger-car population in each province, not vehicle prices or sales volumes.
        </p>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Regional market summary">
        <MetricCard
          metric={{
            label: "Passenger cars shown",
            value: formatNumberCompact(totalPassengerCars),
            helper: "Total across the provinces included in this demo",
            tone: "positive",
          }}
        />
        <MetricCard
          metric={{
            label: "Province with the most cars",
            value: largest.region,
            helper: `${formatNumberCompact(largest.passengerCars)} passenger cars`,
          }}
        />
        <MetricCard
          metric={{
            label: "Provinces included",
            value: String(data.regionalMarket.length),
            helper: "Number of provinces shown in this demo view",
          }}
        />
        <MetricCard
          metric={{
            label: "Average cars per province",
            value: formatNumberCompact(averagePassengerCars),
            helper: "Simple average across the provinces shown",
          }}
        />
      </section>

      <section className="grid gap-5 xl:grid-cols-[1.15fr_0.85fr]">
        <RegionalMarketChart data={data.regionalMarket} />

        <article className="glass-panel min-w-0 rounded-2xl p-4 sm:p-5">
          <h2 className="text-sm font-semibold text-slate-950">Province-by-province comparison</h2>
          <p className="mt-1 text-xs leading-5 text-slate-700">
            These are official public counts of passenger cars. A larger number means more passenger cars are registered in that province.
          </p>

          <div
            className="mt-5 overflow-x-auto rounded-xl border border-white/80 bg-white/70 backdrop-blur-md"
            tabIndex={0}
            aria-label="Scrollable regional comparison table"
          >
            <table className="w-full min-w-[28rem] border-collapse text-left text-xs">
              <caption className="sr-only">Regional passenger-car counts and each province&apos;s share of the provinces shown</caption>
              <thead className="bg-slate-100/90 text-slate-800">
                <tr>
                  <th scope="col" className="px-3 py-3 font-bold">Province</th>
                  <th scope="col" className="px-3 py-3 text-right font-bold">Passenger cars</th>
                  <th scope="col" className="px-3 py-3 text-right font-bold">Share of this view</th>
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
        <h2 className="text-sm font-semibold text-slate-950">What could be added later</h2>
        <div className="mt-5 grid gap-6 md:grid-cols-3">
          <article>
            <div className="text-lg font-semibold text-slate-950">How easy a vehicle is to sell</div>
            <p className="mt-2 text-sm leading-6 text-slate-700">
              Combine the number of cars with active listings and how quickly listings disappear to estimate how active each regional market is.
            </p>
          </article>
          <article>
            <div className="text-lg font-semibold text-slate-950">How quickly prices move</div>
            <p className="mt-2 text-sm leading-6 text-slate-700">
              Track repeated listings and price reductions to see whether sellers are lowering prices over time.
            </p>
          </article>
          <article>
            <div className="text-lg font-semibold text-slate-950">Monitor many vehicles at once</div>
            <p className="mt-2 text-sm leading-6 text-slate-700">
              Compare value changes across many makes, models, years and locations instead of checking one vehicle at a time.
            </p>
          </article>
        </div>
      </section>
    </div>
  );
}
