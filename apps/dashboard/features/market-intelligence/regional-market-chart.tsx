"use client";

import { scaleBand, scaleLinear } from "d3";

import { formatNumberCompact } from "@/lib/format";
import type { RegionalMarketPoint } from "@/lib/types";

export function RegionalMarketChart({ data }: { data: RegionalMarketPoint[] }) {
  const width = 780;
  const rowHeight = 44;
  const height = 36 + data.length * rowHeight;
  const left = 130;
  const right = 40;

  const x = scaleLinear()
    .domain([0, Math.max(...data.map((item) => item.passengerCars))])
    .range([left, width - right]);

  const y = scaleBand()
    .domain(data.map((item) => item.region))
    .range([20, height - 10])
    .padding(0.32);

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5">
      <div className="mb-5">
        <h3 className="text-sm font-semibold text-slate-900">Passenger-car stock by province</h3>
        <p className="mt-1 text-xs leading-5 text-slate-500">
          Official BPS public-table context. Vehicle stock is a market-depth proxy, not a liquidity score by itself.
        </p>
      </div>

      <svg viewBox={`0 0 ${width} ${height}`} className="h-auto w-full" role="img" aria-label="Passenger car stock by province">
        {data.map((item, index) => {
          const py = y(item.region) ?? 0;
          const barWidth = x(item.passengerCars) - left;
          const fill = index === 0 ? "#2563eb" : "#94a3b8";

          return (
            <g key={item.region}>
              <text x="0" y={py + (y.bandwidth() / 2) + 4} className="fill-slate-600 text-[11px] font-medium">
                {item.region}
              </text>
              <rect x={left} y={py} width={Math.max(barWidth, 2)} height={y.bandwidth()} rx="6" fill={fill} />
              <text x={Math.min(x(item.passengerCars) + 10, width - 30)} y={py + (y.bandwidth() / 2) + 4} className="fill-slate-500 text-[11px] font-semibold">
                {formatNumberCompact(item.passengerCars)}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
