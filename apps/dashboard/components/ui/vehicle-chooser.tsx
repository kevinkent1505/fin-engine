"use client";

import { useMemo, useState } from "react";

import type { VehicleCatalog, VehicleOption } from "@/lib/types";

function unique(values: string[]) {
  return [...new Set(values)].sort((a, b) => a.localeCompare(b));
}

function uniqueNumbers(values: number[]) {
  return [...new Set(values)].sort((a, b) => b - a);
}

function sameOption(a: VehicleOption, b: VehicleOption) {
  return (
    a.make === b.make &&
    a.model === b.model &&
    a.year === b.year &&
    a.region === b.region
  );
}

function firstMatching(
  options: VehicleOption[],
  make: string,
  model?: string,
  year?: number,
): VehicleOption | undefined {
  return options.find(
    (option) =>
      option.make === make &&
      (model === undefined || option.model === model) &&
      (year === undefined || option.year === year),
  );
}

export function VehicleChooser({
  catalog,
  selected,
}: {
  catalog: VehicleCatalog;
  selected: VehicleOption;
}) {
  const options = useMemo(
    () =>
      catalog.options.some((option) => sameOption(option, selected))
        ? catalog.options
        : [selected, ...catalog.options],
    [catalog.options, selected],
  );

  const [make, setMake] = useState(selected.make);
  const [model, setModel] = useState(selected.model);
  const [year, setYear] = useState(selected.year);
  const [region, setRegion] = useState(selected.region);

  const makes = useMemo(
    () => unique(options.map((option) => option.make)),
    [options],
  );

  const models = useMemo(
    () =>
      unique(
        options
          .filter((option) => option.make === make)
          .map((option) => option.model),
      ),
    [options, make],
  );

  const years = useMemo(
    () =>
      uniqueNumbers(
        options
          .filter((option) => option.make === make && option.model === model)
          .map((option) => option.year),
      ),
    [options, make, model],
  );

  const regions = useMemo(
    () =>
      unique(
        options
          .filter(
            (option) =>
              option.make === make &&
              option.model === model &&
              option.year === year,
          )
          .map((option) => option.region),
      ),
    [options, make, model, year],
  );

  function chooseMake(nextMake: string) {
    const next = firstMatching(options, nextMake);
    if (!next) return;
    setMake(next.make);
    setModel(next.model);
    setYear(next.year);
    setRegion(next.region);
  }

  function chooseModel(nextModel: string) {
    const next = firstMatching(options, make, nextModel);
    if (!next) return;
    setModel(next.model);
    setYear(next.year);
    setRegion(next.region);
  }

  function chooseYear(nextYear: number) {
    const next = firstMatching(options, make, model, nextYear);
    if (!next) return;
    setYear(next.year);
    setRegion(next.region);
  }

  const sourceLabel =
    catalog.source === "database"
      ? "Marketplace choices"
      : catalog.source === "database_demo"
        ? "Demo marketplace choices"
        : catalog.source === "database_mixed"
          ? "Marketplace + demo choices"
          : catalog.source === "development"
            ? "Demo choices"
            : "Default demo only";

  return (
    <section
      className="glass-panel rounded-2xl p-4 sm:p-5"
      aria-labelledby="vehicle-chooser-title"
    >
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div className="max-w-2xl">
          <div className="text-xs font-black uppercase tracking-[0.14em] text-blue-900">
            Start here
          </div>
          <h2
            id="vehicle-chooser-title"
            className="mt-1 text-lg font-semibold text-slate-950 sm:text-xl"
          >
            Choose the vehicle you want to explore
          </h2>
          <p className="mt-1 text-sm leading-6 text-slate-700">
            Pick a brand, model, year and location. Then press <strong>Show this vehicle</strong>. The dashboard will update the numbers and charts for that selection.
          </p>
        </div>
        <span className="inline-flex min-h-8 w-fit items-center rounded-full border border-slate-400 bg-white px-3 py-1 text-xs font-black text-slate-950">
          {sourceLabel}
        </span>
      </div>

      <form method="get" className="mt-5 grid gap-4 lg:grid-cols-[1fr_1fr_0.8fr_1.2fr_auto] lg:items-end">
        <label className="block">
          <span className="text-sm font-bold text-slate-950">Brand</span>
          <span className="mt-0.5 block text-xs text-slate-600">Who makes the car</span>
          <select
            name="make"
            value={make}
            onChange={(event) => chooseMake(event.target.value)}
            className="mt-2 min-h-11 w-full rounded-xl border border-slate-400 bg-white px-3 py-2 text-sm font-semibold text-slate-950 shadow-sm focus:border-blue-800"
          >
            {makes.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>

        <label className="block">
          <span className="text-sm font-bold text-slate-950">Model</span>
          <span className="mt-0.5 block text-xs text-slate-600">The specific car name</span>
          <select
            name="model"
            value={model}
            onChange={(event) => chooseModel(event.target.value)}
            className="mt-2 min-h-11 w-full rounded-xl border border-slate-400 bg-white px-3 py-2 text-sm font-semibold text-slate-950 shadow-sm focus:border-blue-800"
          >
            {models.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>

        <label className="block">
          <span className="text-sm font-bold text-slate-950">Year</span>
          <span className="mt-0.5 block text-xs text-slate-600">Model year</span>
          <select
            name="year"
            value={year}
            onChange={(event) => chooseYear(Number(event.target.value))}
            className="mt-2 min-h-11 w-full rounded-xl border border-slate-400 bg-white px-3 py-2 text-sm font-semibold text-slate-950 shadow-sm focus:border-blue-800"
          >
            {years.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>

        <label className="block">
          <span className="text-sm font-bold text-slate-950">Location</span>
          <span className="mt-0.5 block text-xs text-slate-600">Where listings are compared</span>
          <select
            name="region"
            value={region}
            onChange={(event) => setRegion(event.target.value)}
            className="mt-2 min-h-11 w-full rounded-xl border border-slate-400 bg-white px-3 py-2 text-sm font-semibold text-slate-950 shadow-sm focus:border-blue-800"
          >
            {regions.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>

        <button type="submit" className="action-primary w-full whitespace-nowrap lg:w-auto">
          Show this vehicle
        </button>
      </form>

      <p className="mt-4 text-xs leading-5 text-slate-600">
        {catalog.detail}
      </p>
    </section>
  );
}
