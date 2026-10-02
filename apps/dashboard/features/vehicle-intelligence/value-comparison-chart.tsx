"use client";

import { scaleLinear } from "d3";

import { formatRupiahCompact } from "@/lib/format";
import type { ValuePoint } from "@/lib/types";

const markerClass = {
  listing: "fill-blue-700",
  njkb: "fill-emerald-700",
  auction_limit: "fill-amber-700",
};

const kindLabel = {
  listing: "Marketplace asking price",
  njkb: "Official NJKB reference",
  auction_limit: "Auction limit reference",
};

export function ValueComparisonChart({ values }: { values: ValuePoint[] }) {
  const min = Math.min(...values.map((item) => item.value)) * 0.9;
  const max = Math.max(...values.map((item) => item.value)) * 1.08;
  const x = scaleLinear().domain([min, max]).range([90, 710]);

  return (
    <figure className="glass-panel min-w-0 overflow-hidden rounded-2xl p-4 sm:p-5">
      <figcaption className="mb-5">
        <h3 className="text-sm font-semibold text-slate-950">Value signal comparison</h3>
        <p className="mt-1 text-xs leading-5 text-slate-600">
          Asking price, NJKB and auction limits remain separate because they represent different economic signals.
        </p>
      </figcaption>

      <div className="chart-scroll" tabIndex={0} aria-label="Scrollable vehicle value comparison chart">
        <svg
          viewBox="0 0 760 220"
          className="h-auto w-full"
          role="img"
          aria-labelledby="value-comparison-title value-comparison-desc"
        >
          <title id="value-comparison-title">Vehicle value signal comparison</title>
          <desc id="value-comparison-desc">
            A comparison of marketplace asking price, official NJKB reference and auction-limit reference for the selected vehicle.
          </desc>

          <line x1="90" x2="710" y1="170" y2="170" className="stroke-slate-300" strokeWidth="2" />
          {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
            const value = min + (max - min) * ratio;
            const px = x(value);
            return (
              <g key={ratio}>
                <line x1={px} x2={px} y1="166" y2="176" className="stroke-slate-400" />
                <text x={px} y="198" textAnchor="middle" className="fill-slate-600 text-[11px]">
                  {formatRupiahCompact(value)}
                </text>
              </g>
            );
          })}

          {values.map((item, index) => {
            const px = x(item.value);
            const y = 36 + index * 46;
            return (
              <g key={item.kind}>
                <text x="10" y={y + 4} className="fill-slate-700 text-[11px] font-semibold">
                  {item.kind === "listing" ? "ASKING" : item.kind === "njkb" ? "NJKB" : "AUCTION"}
                </text>
                <line x1="90" x2={px} y1={y} y2={y} className="stroke-slate-200" strokeWidth="8" strokeLinecap="round" />
                <circle cx={px} cy={y} r="9" className={markerClass[item.kind]} stroke="#ffffff" strokeWidth="2" />
                <text x={Math.min(px + 14, 650)} y={y + 4} className="fill-slate-950 text-[12px] font-bold">
                  {formatRupiahCompact(item.value)}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      <table className="sr-table">
        <caption>Vehicle value comparison data</caption>
        <thead>
          <tr>
            <th scope="col">Signal</th>
            <th scope="col">Value</th>
          </tr>
        </thead>
        <tbody>
          {values.map((item) => (
            <tr key={item.kind}>
              <th scope="row">{kindLabel[item.kind]}</th>
              <td>{formatRupiahCompact(item.value)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </figure>
  );
}
