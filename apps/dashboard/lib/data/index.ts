import {
  requestAnalysisValuation,
  requestAnalysisVehicleOptions,
} from "@/lib/data/analysis";
import { pocDashboardData } from "@/lib/data/poc";
import type {
  DashboardData,
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

/**
 * Server-side data access boundary for dashboard pages.
 *
 * Primary path: Python analysis service. When DATABASE_URL is configured on
 * the analysis service, valuation is produced from latest persisted listing
 * observations in Neon. Without DATABASE_URL the analysis service uses its
 * committed development comparable CSV.
 *
 * Fallback path: clearly-labelled POC fixture. We never silently present the
 * fallback marketplace values as live analysis output.
 */
export async function getDashboardData(
  vehicle: VehicleOption = dashboardVehicle,
): Promise<DashboardData> {
  const analysisResult = await requestAnalysisValuation(vehicle);

  if (analysisResult.status !== "ok") {
    return {
      ...pocDashboardData,
      analysis: {
        state: "fallback",
        label: "Default demo vehicle shown",
        detail: `${analysisResult.detail} The dashboard has returned to its clearly labelled default POC vehicle rather than showing unrelated numbers for your selection.`,
      },
    };
  }

  const result = analysisResult.data;
  const databaseBacked = result.method === "comparable_market_db_v1";
  const confidence = databaseBacked ? "observed" : "illustrative";
  const selectedVehicle: VehicleOption = {
    make: result.vehicle.make,
    model: result.vehicle.model,
    year: result.vehicle.year,
    region: result.region,
  };
  const hasPocReferences = sameVehicle(selectedVehicle, pocReferenceVehicle);

  const listingSignal: ValuePoint = {
    label: databaseBacked
      ? "Marketplace asking median"
      : "Development comparable median",
    value: result.valuation.estimate,
    kind: "listing",
    confidence,
  };

  const referenceSignals = hasPocReferences
    ? pocDashboardData.snapshot.values.filter((item) => item.kind !== "listing")
    : [];

  const analysisSource: SourceDescriptor = {
    id: "fin_engine_analysis",
    name: "Fin Engine analysis engine",
    type: databaseBacked
      ? "Neon-backed marketplace comparable valuation"
      : "Development comparable valuation",
    confidence,
    lastUpdated: "Current dashboard request",
    note: databaseBacked
      ? "The estimate uses the latest stored price for each matching marketplace listing, so repeated crawls do not count the same listing multiple times."
      : "The dashboard is connected to the analysis service, but that service is using its development comparison dataset because Neon is not configured there.",
  };

  const allowedReferenceSourceIds = new Set(
    hasPocReferences
      ? ["bps_vehicle_stock_2023", "kemendagri_njkb_2025", "auction_poc"]
      : ["bps_vehicle_stock_2023"],
  );

  return {
    ...pocDashboardData,
    mode: "analysis",
    analysis: {
      state: databaseBacked ? "database" : "development",
      method: result.method,
      label: databaseBacked
        ? "Marketplace data connected"
        : "Demo comparison data connected",
      detail: databaseBacked
        ? `${result.sample_size} marketplace listings matching this vehicle are feeding the estimate.`
        : `${result.sample_size} development comparison rows match this vehicle. Connect the analysis service to Neon for observed marketplace data.`,
    },
    snapshot: {
      ...pocDashboardData.snapshot,
      make: result.vehicle.make,
      model: result.vehicle.model,
      year: result.vehicle.year,
      region: result.region,
      variant: hasPocReferences
        ? pocDashboardData.snapshot.variant
        : "All matching listings for this model",
      sampleSize: result.sample_size,
      observedRange: [result.valuation.low, result.valuation.high],
      lastRefresh: databaseBacked
        ? "Stored marketplace listings"
        : "Development comparison dataset",
      values: [listingSignal, ...referenceSignals],
      priceHistory: [
        {
          date: "Current",
          value: result.valuation.estimate,
        },
      ],
    },
    sources: [
      ...pocDashboardData.sources.filter((source) =>
        allowedReferenceSourceIds.has(source.id),
      ),
      analysisSource,
    ],
  };
}

export async function getVehicleSnapshot(vehicle?: VehicleOption) {
  const data = await getDashboardData(vehicle);
  return data.snapshot;
}

export async function getRegionalMarket() {
  const data = await getDashboardData();
  return data.regionalMarket;
}

export async function getSources(vehicle?: VehicleOption) {
  const data = await getDashboardData(vehicle);
  return data.sources;
}
