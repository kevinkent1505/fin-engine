import type { DataConfidence } from "@/lib/types";

const confidenceClass: Record<DataConfidence, string> = {
  official: "border-emerald-200 bg-emerald-50 text-emerald-700",
  observed: "border-blue-200 bg-blue-50 text-blue-700",
  illustrative: "border-amber-200 bg-amber-50 text-amber-700",
};

export function SourceBadge({ confidence }: { confidence: DataConfidence }) {
  return (
    <span
      className={`inline-flex rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.12em] ${confidenceClass[confidence]}`}
    >
      {confidence}
    </span>
  );
}
