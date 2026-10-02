"use client";

import { scaleLinear } from "d3";

import { formatRupiahCompact } from "@/lib/format";
import type { ValuePoint } from "@/lib/types";

const markerClass = {
  listing: "fill-blue-600",
  njkb: "fill-emerald-600",
  auction_limit: "fill-amber-600",
};

export function ValueComparisonChart({ values }: { values: ValuePoint[] }) {
  const min = Math.min(...values.map((item) => item.value)) * 0.9;
  const max = Math.max(...values.map((item) => item.value)) * 1.08;
  const x = scaleLinear().domain([min, max]).range([70, 710]);

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white p-5">
      <div className="mb-5 flex items-start justify-between gap-4">
        <div>
          <h3 className="text-sm font-semibold text-slate-900">Value signal comparison</h3>
          <p className="mt-1 text-xs leading-5 text-slate-500">
            Signals are shown separately because asking price, NJKB and auction limits are not economically equivalent.
          </p>
        </div>
      </div>

      <svg viewBox="0 0 760 220" className="h-auto w-full" role="img" aria-label="Vehicle value comparison">
        <line x1="70" x2="710" y1="170" y2="170" className="stroke-slate-200" strokeWidth="2" />
        {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
          const value = min + (max - min) * ratio;
          const px = x(value);
          return (
            <g key={ratio}>
              <line x1={px} x2={px} y1="166" y2="176" className="stroke-slate-300" />
              <text x={px} y="198" textAnchor="middle" className="fill-slate-400 text-[11px]">
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
              <text x="10" y={y + 4} className="fill-slate-500 text-[11px] font-medium">
                {item.kind === "listing" ? "ASKING" : item.kind === "njkb" ? "NJKB" : "AUCTION"}
              </text>
              <line x1="70" x2={px} y1={y} y2={y} className="stroke-slate-100" strokeWidth="8" strokeLinecap="round" />
              <circle cx={px} cy={y} r="8" className={markerClass[item.kind]} />
              <text x={Math.min(px + 14, 650)} y={y + 4} className="fill-slate-900 text-[12px] font-semibold">
                {formatRupiahCompact(item.value)}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
