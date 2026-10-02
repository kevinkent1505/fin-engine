"use client";

import { area, curveMonotoneX, line, scaleLinear, scalePoint } from "d3";

import { formatRupiahCompact } from "@/lib/format";
import type { HistoricalPricePoint } from "@/lib/types";

export function PriceHistoryChart({ data }: { data: HistoricalPricePoint[] }) {
  const width = 760;
  const height = 250;
  const left = 60;
  const right = 20;
  const top = 24;
  const bottom = 42;

  const x = scalePoint<string>()
    .domain(data.map((item) => item.date))
    .range([left, width - right]);

  const values = data.map((item) => item.value);
  const min = Math.min(...values) * 0.97;
  const max = Math.max(...values) * 1.03;
  const y = scaleLinear().domain([min, max]).range([height - bottom, top]);

  const path = line<HistoricalPricePoint>()
    .x((item) => x(item.date) ?? left)
    .y((item) => y(item.value))
    .curve(curveMonotoneX)(data);

  const fillPath = area<HistoricalPricePoint>()
    .x((item) => x(item.date) ?? left)
    .y0(height - bottom)
    .y1((item) => y(item.value))
    .curve(curveMonotoneX)(data);

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5">
      <div>
        <h3 className="text-sm font-semibold text-slate-900">Observed asking-price trend</h3>
        <p className="mt-1 text-xs text-slate-500">POC illustrative series until repeated marketplace observations are live.</p>
      </div>

      <svg viewBox={`0 0 ${width} ${height}`} className="mt-4 h-auto w-full" role="img" aria-label="Vehicle price history">
        <defs>
          <linearGradient id="price-area" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="#2563eb" stopOpacity="0.18" />
            <stop offset="100%" stopColor="#2563eb" stopOpacity="0" />
          </linearGradient>
        </defs>

        {fillPath ? <path d={fillPath} fill="url(#price-area)" /> : null}
        {path ? <path d={path} fill="none" stroke="#2563eb" strokeWidth="3" /> : null}

        {data.map((item) => {
          const px = x(item.date) ?? left;
          const py = y(item.value);
          return (
            <g key={item.date}>
              <circle cx={px} cy={py} r="4.5" fill="#2563eb" />
              <text x={px} y={height - 16} textAnchor="middle" className="fill-slate-400 text-[11px]">
                {item.date}
              </text>
            </g>
          );
        })}

        <text x={left} y="16" className="fill-slate-400 text-[11px]">
          {formatRupiahCompact(max)}
        </text>
        <text x={left} y={height - bottom - 7} className="fill-slate-400 text-[11px]">
          {formatRupiahCompact(min)}
        </text>
      </svg>
    </div>
  );
}
