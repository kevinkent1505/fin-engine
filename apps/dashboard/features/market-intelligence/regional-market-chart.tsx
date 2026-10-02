"use client";

import { scaleBand, scaleLinear } from "d3";

import { formatNumberCompact } from "@/lib/format";
import type { RegionalMarketPoint } from "@/lib/types";

export function RegionalMarketChart({ data }: { data: RegionalMarketPoint[] }) {
  const width = 780;
  const rowHeight = 44;
  const height = 36 + data.length * rowHeight;
  const left = 145;
  const right = 46;

  const x = scaleLinear()
    .domain([0, Math.max(...data.map((item) => item.passengerCars))])
    .range([left, width - right]);

  const y = scaleBand()
    .domain(data.map((item) => item.region))
    .range([20, height - 10])
    .padding(0.32);

  return (
    <figure className="glass-panel min-w-0 overflow-hidden rounded-2xl p-4 sm:p-5">
      <figcaption className="mb-5">
        <h3 className="text-sm font-semibold text-slate-950">Passenger-car stock by province</h3>
        <p className="mt-1 text-xs leading-5 text-slate-600">
          Official BPS public-table context. Vehicle stock is a market-depth proxy, not a liquidity score by itself.
        </p>
      </figcaption>

      <div className="chart-scroll" tabIndex={0} aria-label="Scrollable passenger-car stock chart">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="h-auto w-full"
          role="img"
          aria-labelledby="regional-market-title regional-market-desc"
        >
          <title id="regional-market-title">Passenger-car stock by province</title>
          <desc id="regional-market-desc">
            Horizontal bars compare official passenger-car stock across the selected Indonesian provinces.
          </desc>

          {data.map((item, index) => {
            const py = y(item.region) ?? 0;
            const barWidth = x(item.passengerCars) - left;
            const fill = index === 0 ? "#1d4ed8" : "#64748b";

            return (
              <g key={item.region}>
                <text x="0" y={py + y.bandwidth() / 2 + 4} className="fill-slate-700 text-[11px] font-semibold">
                  {item.region}
                </text>
                <rect x={left} y={py} width={Math.max(barWidth, 2)} height={y.bandwidth()} rx="6" fill={fill} />
                <text
                  x={Math.min(x(item.passengerCars) + 10, width - 42)}
                  y={py + y.bandwidth() / 2 + 4}
                  className="fill-slate-700 text-[11px] font-bold"
                >
                  {formatNumberCompact(item.passengerCars)}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      <table className="sr-table">
        <caption>Passenger-car stock by province data</caption>
        <thead>
          <tr>
            <th scope="col">Province</th>
            <th scope="col">Passenger cars</th>
          </tr>
        </thead>
        <tbody>
          {data.map((item) => (
            <tr key={item.region}>
              <th scope="row">{item.region}</th>
              <td>{new Intl.NumberFormat("en").format(item.passengerCars)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </figure>
  );
}
