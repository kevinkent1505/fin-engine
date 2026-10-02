import type { DataConfidence } from "@/lib/types";

const confidenceClass: Record<DataConfidence, string> = {
  official: "border-emerald-300/80 bg-emerald-50/90 text-emerald-900",
  observed: "border-blue-300/80 bg-blue-50/90 text-blue-900",
  illustrative: "border-amber-300/80 bg-amber-50/90 text-amber-900",
};

const confidenceLabel: Record<DataConfidence, string> = {
  official: "Official source",
  observed: "Observed data",
  illustrative: "Illustrative POC data",
};

export function SourceBadge({ confidence }: { confidence: DataConfidence }) {
  return (
    <span
      className={`inline-flex min-h-8 items-center rounded-full border px-2.5 py-1 text-[11px] font-bold uppercase tracking-[0.1em] ${confidenceClass[confidence]}`}
      aria-label={confidenceLabel[confidence]}
    >
      {confidence}
    </span>
  );
}
