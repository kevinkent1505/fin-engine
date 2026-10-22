import {
  requestAnalysisRegionalMarket,
  requestAnalysisValuation,
  requestAnalysisVehicleOptions,
} from "@/lib/data/analysis";
import { pocDashboardData } from "@/lib/data/poc";
import type {
  DashboardData,
  RegionalMarketPoint,
  SourceDescriptor,
  ValuePoint,
  VehicleCatalog,
  VehicleOption,
} from "@/lib/types";

const dashboardVehicle: VehicleOption = {
  make: process.env.DASHBOARD_VEHICLE_MAKE ?? "Toyota",
  model: process.env.DASHBOARD_VEHICLE_MODEL ?? "Avanza",
  year: Number(process.env.DASHBOARD_VEHICLE_YEAR ?? "2025"),
  region: process.env.DASHBOARD_VEHICLE_REGION ?? "DKI Jakarta",
};

const pocReferenceVehicle: VehicleOption = {
  make: pocDashboardData.snapshot.make,
  model: pocDashboardData.snapshot.model,
  year: pocDashboardData.snapshot.year,
  region: pocDashboardData.snapshot.region,
};

function sameVehicle(a: VehicleOption, b: VehicleOption) {
  return (
    a.make.toLowerCase() === b.make.toLowerCase() &&
    a.model.toLowerCase() === b.model.toLowerCase() &&
    a.year === b.year &&
    a.region.toLowerCase() === b.region.toLowerCase()
  );
}

function sameMakeModel(a: VehicleOption, b: VehicleOption) {
  return (
    a.make.toLowerCase() === b.make.toLowerCase() &&
    a.model.toLowerCase() === b.model.toLowerCase()
  );
}

function similarRegion(a: string, b: string) {
  const left = a.trim().toLowerCase();
  const right = b.trim().toLowerCase();
  return left === right || left.includes(right) || right.includes(left);
}

export async function getVehicleCatalog(): Promise<VehicleCatalog> {
  const result = await requestAnalysisVehicleOptions();

  if (result.status === "ok" && result.data.vehicles.length > 0) {
    if (result.data.source === "database_demo") {
      return {
        options: result.data.vehicles,
        source: "database_demo",
        detail:
          "Vehicle choices come from synthetic marketplace records stored in Neon for this POC. They are demo records, not live marketplace observations.",
      };
    }

    if (result.data.source === "database_mixed") {
      return {
        options: result.data.vehicles,
        source: "database_mixed",
        detail:
          "Vehicle choices include both real persisted marketplace records and synthetic POC records. Each selected valuation is labelled according to the evidence actually used.",
      };
    }

    const databaseBacked = result.data.source === "database";
    return {
      options: result.data.vehicles,
      source: result.data.source,
      detail: databaseBacked
        ? "Vehicle choices come from marketplace listing records currently stored in Neon."
        : "Vehicle choices come from the development comparable dataset because the analysis service is not connected to Neon.",
    };
  }

  return {
    options: [pocReferenceVehicle],
    source: "fallback",
    detail:
      result.status === "unavailable"
        ? `${result.detail} Only the default demo vehicle is available until the analysis engine reconnects.`
        : "Only the default demo vehicle is available.",
  };
}

export function resolveVehicleSelection(
  requested: Partial<Record<keyof VehicleOption, string | number | undefined>>,
  options: VehicleOption[],
): VehicleOption {
  const requestedYear = Number(requested.year);
  const exact = options.find(
    (option) =>
      typeof requested.make === "string" &&
      typeof requested.model === "string" &&
      typeof requested.region === "string" &&
      Number.isFinite(requestedYear) &&
      option.make.toLowerCase() === requested.make.toLowerCase() &&
      option.model.toLowerCase() === requested.model.toLowerCase() &&
      option.year === requestedYear &&
      option.region.toLowerCase() === requested.region.toLowerCase(),
  );

  if (exact) {
    return exact;
  }

  const configuredDefault = options.find((option) =>
    sameVehicle(option, dashboardVehicle),
  );
  if (configuredDefault) {
    return configuredDefault;
  }

  const closestConfiguredModel = options.find(
    (option) =>
      sameMakeModel(option, dashboardVehicle) &&
      similarRegion(option.region, dashboardVehicle.region),
  );
  if (closestConfiguredModel) {
    return closestConfiguredModel;
  }

  const sameConfiguredModel = options.find((option) =>
    sameMakeModel(option, dashboardVehicle),
  );

  return sameConfiguredModel ?? options[0] ?? pocReferenceVehicle;
}

function bpsFallbackSource(): SourceDescriptor {
  const fixture = pocDashboardData.sources.find((source) =>
    source.id.startsWith("bps_vehicle_stock_"),
  );

  return {
    id: "bps_vehicle_stock_2023_static_fallback",
    name: fixture?.name ?? "Badan Pusat Statistik",
    type: "Regional vehicle stock (bundled reference)",
    confidence: "official",
    lastUpdated: "2023 BPS table · bundled fallback",
    note:
      "Historical 2023 BPS counts bundled with the dashboard are shown because the persisted regional snapshot is unavailable. They are official historical figures, not a live Neon refresh.",
    url: fixture?.url,
  };
}

export async function getRegionalMarketData(): Promise<{
  regionalMarket: RegionalMarketPoint[];
  regionalSource: SourceDescriptor;
  isFallback: boolean;
}> {
  const result = await requestAnalysisRegionalMarket();

  if (result.status !== "ok" || result.data.regions.length === 0) {
    return {
      regionalMarket: pocDashboardData.regionalMarket,
      regionalSource: bpsFallbackSource(),
      isFallback: true,
    };
  }

  return {
    regionalMarket: result.data.regions.map((point) => ({
      region: point.region,
      passengerCars: point.passenger_cars,
    })),
    regionalSource: {
      id: result.data.source,
      name: "Badan Pusat Statistik",
      type: "Official regional vehicle stock",
      confidence: "official",
      lastUpdated: `${result.data.year} BPS table · persisted snapshot`,
      note:
        "Passenger-car counts come from the official BPS table persisted in Neon. They indicate regional vehicle stock, not market prices or sales.",
      url: result.data.source_url,
    },
    isFallback: false,
  };
}

/**
 * Server-side data access boundary for dashboard pages.
 *
 * Marketplace valuation remains synthetic for the POC when demo records are
 * selected. Official regional market context is independently loaded from the
 * latest BPS snapshot persisted in Neon, with the committed fixture retained
 * only as an availability fallback.
 */
export async function getDashboardData(
  vehicle: VehicleOption = dashboardVehicle,
): Promise<DashboardData> {
  const [analysisResult, { regionalMarket, regionalSource }] = await Promise.all([
    requestAnalysisValuation(vehicle),
    getRegionalMarketData(),
  ]);

  if (analysisResult.status === "not_found") {
    return {
      mode: "unavailable",
      analysis: {
        state: "no_data",
        label: "No matching valuation available",
        detail: `${analysisResult.detail} No demo price has been substituted. Choose another vehicle or add matching listing observations to the analysis source.`,
      },
      snapshot: {
        make: vehicle.make,
        model: vehicle.model,
        year: vehicle.year,
        region: vehicle.region,
        variant: "No matching comparables",
        sampleSize: 0,
        values: [],
        priceHistory: [],
        observedRange: [0, 0],
        lastRefresh: "No valuation available",
      },
      regionalMarket,
      sources: [regionalSource],
    };
  }

  if (analysisResult.status !== "ok") {
    return {
      ...pocDashboardData,
      regionalMarket,
      sources: [
        regionalSource,
        ...pocDashboardData.sources.filter(
          (source) => !source.id.startsWith("bps_vehicle_stock_"),
        ),
      ],
      analysis: {
        state: "fallback",
        label: "Default demo vehicle shown",
        detail: `${analysisResult.detail} The analysis service is unavailable, so a separate, clearly labelled default demo vehicle is shown. Its values do not describe your previous selection.`,
      },
    };
  }

  const result = analysisResult.data;
  const observedDatabaseBacked = result.method === "comparable_market_db_v1";
  const syntheticDatabaseBacked =
    result.method === "comparable_market_demo_db_v1";
  const confidence = observedDatabaseBacked ? "observed" : "illustrative";

  const listingSignal: ValuePoint = {
    label: observedDatabaseBacked
      ? "Marketplace asking median"
      : syntheticDatabaseBacked
        ? "Synthetic marketplace median"
        : "Development comparable median",
    value: result.valuation.estimate,
    kind: "listing",
    confidence,
  };

  const analysisSource: SourceDescriptor = {
    id: "fin_engine_analysis",
    name: "Fin Engine analysis engine",
    type: observedDatabaseBacked
      ? "Marketplace comparable valuation"
      : syntheticDatabaseBacked
        ? "Synthetic marketplace comparable valuation"
        : "Development comparable valuation",
    confidence,
    lastUpdated: "Current dashboard request",
    note: observedDatabaseBacked
      ? "The estimate uses the latest stored price for each matching marketplace listing, so repeated crawls do not count the same listing multiple times."
      : syntheticDatabaseBacked
        ? "The estimate is calculated from synthetic POC listing records stored in Neon. These prices are generated for demonstration and are not scraped or observed marketplace prices."
        : "The dashboard is connected to the analysis service, but that service is using its development comparison dataset because Neon is not configured there.",
  };

  return {
    ...pocDashboardData,
    mode: "analysis",
    regionalMarket,
    analysis: {
      state: observedDatabaseBacked
        ? "database"
        : syntheticDatabaseBacked
          ? "demo"
          : "development",
      method: result.method,
      label: observedDatabaseBacked
        ? "Marketplace data connected"
        : syntheticDatabaseBacked
          ? "Demo marketplace data connected"
          : "Demo comparison data connected",
      detail: observedDatabaseBacked
        ? `${result.sample_size} marketplace listings matching this vehicle are feeding the estimate.`
        : syntheticDatabaseBacked
          ? `${result.sample_size} synthetic POC listings matching this vehicle are feeding the estimate. No live marketplace scrape is represented.`
          : `${result.sample_size} development comparison rows match this vehicle. Connect the analysis service to Neon for persisted listing data.`,
    },
    snapshot: {
      ...pocDashboardData.snapshot,
      make: result.vehicle.make,
      model: result.vehicle.model,
      year: result.vehicle.year,
      region: result.region,
      variant: "All matching listings for this model",
      sampleSize: result.sample_size,
      observedRange: [result.valuation.low, result.valuation.high],
      lastRefresh: observedDatabaseBacked
        ? "Stored marketplace listings"
        : syntheticDatabaseBacked
          ? "Synthetic POC marketplace dataset"
          : "Development comparison dataset",
      values: [listingSignal],
      priceHistory: [
        {
          date: "Current",
          value: result.valuation.estimate,
        },
      ],
    },
    sources: [regionalSource, analysisSource],
  };
}

export async function getVehicleSnapshot(vehicle?: VehicleOption) {
  const data = await getDashboardData(vehicle);
  return data.snapshot;
}

export async function getRegionalMarket() {
  const { regionalMarket } = await getRegionalMarketData();
  return regionalMarket;
}

export async function getSources(vehicle?: VehicleOption) {
  const data = await getDashboardData(vehicle);
  return data.sources;
}
