import { MetricCard } from "@/components/ui/metric-card";
import { VehicleChooser } from "@/components/ui/vehicle-chooser";
import {
  requestAnalysisReferences,
  requestOfficialVehicleOptions,
} from "@/lib/data/analysis";
import { formatRupiahCompact } from "@/lib/format";
import type { VehicleCatalog, VehicleOption } from "@/lib/types";

function selectVehicle(
  options: VehicleOption[],
  query: Record<string, string | string[] | undefined>,
): VehicleOption | undefined {
  const make = typeof query.make === "string" ? query.make : undefined;
  const model = typeof query.model === "string" ? query.model : undefined;
  const year = typeof query.year === "string" ? Number(query.year) : undefined;
  const region = typeof query.region === "string" ? query.region : undefined;

  const exact = options.find(
    (option) =>
      make !== undefined &&
      model !== undefined &&
      Number.isFinite(year) &&
      option.make.toLowerCase() === make.toLowerCase() &&
      option.model.toLowerCase() === model.toLowerCase() &&
      option.year === year &&
      (region === undefined || option.region.toLowerCase() === region.toLowerCase()),
  );

  if (exact) return exact;

  return (
    options.find(
      (option) =>
        option.make.toLowerCase() === "toyota" &&
        option.model.toLowerCase() === "avanza" &&
        option.year === 2025,
    ) ?? options[0]
  );
}

function unavailablePanel(detail: string) {
  return (
    <div className="glass-panel rounded-2xl p-5">
      <div className="text-xs font-bold uppercase tracking-[0.18em] text-amber-800">
        Official data unavailable
      </div>
      <h1 className="mt-2 text-2xl font-semibold tracking-tight text-slate-950 sm:text-3xl">
        Fin Engine could not load the official vehicle dataset.
      </h1>
      <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-700">{detail}</p>
      <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-700">
        No synthetic or demo vehicle values are substituted on this page.
      </p>
    </div>
  );
}

export default async function OfficialReferencesPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const query = await searchParams;
  const catalogResult = await requestOfficialVehicleOptions();

  if (catalogResult.status !== "ok" || catalogResult.data.vehicles.length === 0) {
    return unavailablePanel(
      catalogResult.status === "unavailable"
        ? catalogResult.detail
        : "No official NJKB vehicle records were returned.",
    );
  }

  const catalog: VehicleCatalog = {
    options: catalogResult.data.vehicles,
    source: "official",
    detail:
      "Vehicle choices come only from official NJKB records persisted from the government source. Synthetic marketplace records are not used here.",
  };

  const selected = selectVehicle(catalog.options, query);
  if (!selected) {
    return unavailablePanel("The official vehicle catalog is empty.");
  }

  const referencesResult = await requestAnalysisReferences({
    make: selected.make,
    model: selected.model,
    year: selected.year,
  });

  if (referencesResult.status !== "ok") {
    return unavailablePanel(referencesResult.detail);
  }

  const njkb = referencesResult.data.njkb;
  const valueLabel =
    njkb.status === "exact" && njkb.value !== null
      ? formatRupiahCompact(njkb.value)
      : njkb.status === "range" && njkb.low !== null && njkb.high !== null
        ? `${formatRupiahCompact(njkb.low)}–${formatRupiahCompact(njkb.high)}`
        : "Not available";

  const lowLabel =
    njkb.low !== null ? formatRupiahCompact(njkb.low) : "Not available";
  const highLabel =
    njkb.high !== null ? formatRupiahCompact(njkb.high) : "Not available";

  return (
    <div className="space-y-6 sm:space-y-7">
      <section>
        <div className="text-xs font-bold uppercase tracking-[0.18em] text-blue-900">
          Official vehicle intelligence
        </div>
        <h1 className="mt-2 max-w-4xl text-2xl font-semibold tracking-tight text-slate-950 sm:text-3xl md:text-4xl">
          Explore official NJKB reference values without synthetic market data.
        </h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-700 md:text-base">
          The values on this page come from persisted official government records. When multiple official variants exist for the same model and year, Fin Engine shows the full range instead of guessing a variant.
        </p>
      </section>

      <VehicleChooser catalog={catalog} selected={selected} />

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Official NJKB summary">
        <MetricCard
          metric={{
            label: "Official NJKB",
            value: valueLabel,
            helper:
              njkb.status === "range"
                ? "Official range across all matched variants for this make, model and year"
                : "Official reference value for this make, model and year",
            tone: "positive",
          }}
        />
        <MetricCard
          metric={{
            label: "Official variants",
            value: String(njkb.candidate_count),
            helper: "Number of persisted official records matched to this model-year",
          }}
        />
        <MetricCard
          metric={{
            label: "Lowest NJKB",
            value: lowLabel,
            helper: "Lowest official reference among the matched variants",
          }}
        />
        <MetricCard
          metric={{
            label: "Highest NJKB",
            value: highLabel,
            helper: "Highest official reference among the matched variants",
          }}
        />
      </section>

      <section className="grid gap-5 xl:grid-cols-[1.15fr_0.85fr]">
        <article className="glass-panel min-w-0 rounded-2xl p-4 sm:p-5">
          <h2 className="text-sm font-semibold text-slate-950">Matched official variants</h2>
          <p className="mt-1 text-xs leading-5 text-slate-700">
            Variant names below are preserved from the official reference dataset. Fin Engine does not collapse them into an invented single configuration.
          </p>

          <div className="mt-5 flex flex-wrap gap-2">
            {njkb.variants.length > 0 ? (
              njkb.variants.map((variant) => (
                <span
                  key={variant}
                  className="inline-flex min-h-8 items-center rounded-full border border-slate-300 bg-white/80 px-3 py-1 text-xs font-semibold text-slate-900"
                >
                  {variant}
                </span>
              ))
            ) : (
              <span className="text-sm text-slate-700">No variant labels were supplied by the source.</span>
            )}
          </div>
        </article>

        <article className="glass-panel min-w-0 rounded-2xl p-4 sm:p-5">
          <h2 className="text-sm font-semibold text-slate-950">Source provenance</h2>
          <div className="mt-4 space-y-3 text-sm leading-6 text-slate-700">
            <p>
              <strong className="text-slate-950">Source:</strong> official NJKB government reference data.
            </p>
            <p>
              <strong className="text-slate-950">Coverage:</strong> {selected.make} {selected.model} {selected.year}, Indonesia.
            </p>
            <p>
              <strong className="text-slate-950">Matching rule:</strong> exact make, model and year. Variant ambiguity is exposed as a range rather than hidden.
            </p>
          </div>
          {njkb.source_urls.map((url) => (
            <a
              key={url}
              href={url}
              target="_blank"
              rel="noreferrer"
              className="mt-4 block break-all text-sm font-semibold text-blue-900 underline underline-offset-4"
            >
              Open official source
            </a>
          ))}
        </article>
      </section>
    </div>
  );
}
