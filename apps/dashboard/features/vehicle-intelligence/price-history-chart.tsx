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
  const hasHistory = data.length > 1;

  const x = scalePoint<string>()
    .domain(data.map((item) => item.date))
    .range([left, width - right]);

  const values = data.map((item) => item.value);
  const min = Math.min(...values) * 0.97;
  const max = Math.max(...values) * 1.03;
  const y = scaleLinear().domain([min, max]).range([height - bottom, top]);

  const path = hasHistory
    ? line<HistoricalPricePoint>()
        .x((item) => x(item.date) ?? left)
        .y((item) => y(item.value))
        .curve(curveMonotoneX)(data)
    : null;

  const fillPath = hasHistory
    ? area<HistoricalPricePoint>()
        .x((item) => x(item.date) ?? left)
        .y0(height - bottom)
        .y1((item) => y(item.value))
        .curve(curveMonotoneX)(data)
    : null;

  const title = hasHistory ? "Observed asking-price trend" : "Current asking-price signal";
  const description = hasHistory
    ? "Repeated marketplace observations are shown over time."
    : "The analysis engine currently exposes the valuation snapshot only. Historical database observations will be added to this view when the analysis API exposes a time series.";

  return (
    <figure className="glass-panel min-w-0 overflow-hidden rounded-2xl p-4 sm:p-5">
      <figcaption>
        <h3 className="text-sm font-semibold text-slate-950">{title}</h3>
        <p className="mt-1 text-xs leading-5 text-slate-700">{description}</p>
      </figcaption>

      <div className="chart-scroll mt-4" tabIndex={0} aria-label={`Scrollable ${title.toLowerCase()} chart`}>
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="h-auto w-full"
          role="img"
          aria-labelledby="price-history-title price-history-desc"
        >
          <title id="price-history-title">{title}</title>
          <desc id="price-history-desc">{description}</desc>
          <defs>
            <linearGradient id="price-area" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor="#1d4ed8" stopOpacity="0.24" />
              <stop offset="100%" stopColor="#1d4ed8" stopOpacity="0" />
            </linearGradient>
          </defs>

          {fillPath ? <path d={fillPath} fill="url(#price-area)" /> : null}
          {path ? <path d={path} fill="none" stroke="#1d4ed8" strokeWidth="3" /> : null}

          {data.map((item) => {
            const px = x(item.date) ?? width / 2;
            const py = y(item.value);
            return (
              <g key={item.date}>
                <circle cx={px} cy={py} r={hasHistory ? 5 : 8} fill="#1d4ed8" stroke="#ffffff" strokeWidth="2" />
                <text x={px} y={py - 16} textAnchor="middle" className="fill-slate-950 text-[12px] font-bold">
                  {formatRupiahCompact(item.value)}
                </text>
                <text x={px} y={height - 16} textAnchor="middle" className="fill-slate-700 text-[11px]">
                  {item.date}
                </text>
              </g>
            );
          })}

          <text x={left} y="16" className="fill-slate-700 text-[11px]">
            {formatRupiahCompact(max)}
          </text>
          <text x={left} y={height - bottom - 7} className="fill-slate-700 text-[11px]">
            {formatRupiahCompact(min)}
          </text>
        </svg>
      </div>

      <table className="sr-table">
        <caption>{hasHistory ? "Vehicle asking-price history data" : "Current vehicle asking-price analysis data"}</caption>
        <thead>
          <tr>
            <th scope="col">Date</th>
            <th scope="col">Asking price</th>
          </tr>
        </thead>
        <tbody>
          {data.map((item) => (
            <tr key={item.date}>
              <th scope="row">{item.date}</th>
              <td>{formatRupiahCompact(item.value)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </figure>
  );
}