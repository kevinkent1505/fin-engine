import type { VehicleOption } from "@/lib/types";

export function ValuationUnavailable({ vehicle }: { vehicle: VehicleOption }) {
  return (
    <section
      className="glass-panel rounded-2xl border border-slate-300 p-5 sm:p-7"
      aria-labelledby="valuation-unavailable-title"
      role="status"
    >
      <div className="inline-flex rounded-full border border-slate-400 bg-slate-100 px-3 py-1 text-xs font-bold uppercase tracking-wide text-slate-900">
        No matched listing evidence
      </div>
      <h2
        id="valuation-unavailable-title"
        className="mt-4 text-xl font-semibold text-slate-950 sm:text-2xl"
      >
        No valuation is available for this selection.
      </h2>
      <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-700">
        Fin Engine did not find comparable listings for{" "}
        <strong>
          {vehicle.make} {vehicle.model} {vehicle.year}
        </strong>{" "}
        in <strong>{vehicle.region}</strong>. An estimated price, price range or
        historical trend would be misleading, so none is shown.
      </p>
      <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-700">
        Choose another available vehicle above, or populate the analysis source
        with matching, authorized marketplace observations. Regional public data
        can still be explored independently on the Market page.
      </p>
    </section>
  );
}
