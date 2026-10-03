import {
  requestAnalysisReferences,
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
  VehicleReferenceMatch,
  VehicleReferences,
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

function unavailableReference(): VehicleReferenceMatch {
  return {
    status: "unavailable",
    candidateCount: 0,
    variants: [],
    sourceKeys: [],
    sourceUrls: [],
  };
}

function toReferenceMatch(band: {
  status: "exact" | "range" | "unavailable";
  value: number | null;
  low: number | null;
  high: number | null;
  candidate_count: number;
  variants: string[];
  source_keys: string[];
  source_urls: string[];
}): VehicleReferenceMatch {
  return {
    status: band.status,
    value: band.value ?? undefined,
    low: band.low ?? undefined,
    high: band.high ?? undefined,
    candidateCount: band.candidate_count,
    variants: band.variants,
    sourceKeys: band.source_keys,
    sourceUrls: band.source_urls,
  };
}

function unavailableReferences(): VehicleReferences {
  return {
    njkb: unavailableReference(),
    auctionLimit: unavailableReference(),
  };
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
  return (
    pocDashboardData.sources.find((source) =>
      source.id.startsWith("bps_vehicle_stock_"),
    ) ?? {
      id: "bps_vehicle_stock_fallback",
      name: "Badan Pusat Statistik",
      type: "Regional vehicle stock",
      confidence: "official",
      lastUpdated: "Fallback fixture",
      note: "Static fallback used because the persisted BPS snapshot is unavailable.",
    }
  );
}

function referenceSources(references: VehicleReferences): SourceDescriptor[] {
  const sources: SourceDescriptor[] = [];

  if (references.njkb.status !== "unavailable") {
    sources.push({
      id: references.njkb.sourceKeys[0] ?? "kemendagri_njkb",
      name: "Kemendagri NJKB",
      type: "Official vehicle reference value",
      confidence: "official",
      lastUpdated: "Latest persisted reference snapshot",
      note:
        references.njkb.status === "exact"
          ? "A single official NJKB value is available for this make, model and year."
          : `${references.njkb.candidateCount} official NJKB variant records match this make, model and year. The dashboard shows their range instead of guessing which variant applies.`,
      url: references.njkb.sourceUrls[0],
    });
  }

  if (references.auctionLimit.status !== "unavailable") {
    sources.push({
      id: references.auctionLimit.sourceKeys[0] ?? "djp_vehicle_auction_limits",
      name: "DJP auction reference",
      type: "Official auction / downside reference",
      confidence: "official",
      lastUpdated: "Latest persisted reference snapshot",
      note:
        references.auctionLimit.status === "exact"
          ? "A single auction reference is available for this make, model and year."
          : `${references.auctionLimit.candidateCount} auction reference records match this make, model and year. The dashboard shows their range instead of selecting one arbitrarily.`,
      url: references.auctionLimit.sourceUrls[0],
    });
  }

  return sources;
}

/**
 * Server-side data access boundary for dashboard pages.
 *
 * Marketplace valuation remains synthetic for the POC when demo records are
 * selected. Official reference data is resolved separately from persisted
 * Neon records. Ambiguous model-year references are represented as ranges,
 * never as a guessed variant match.
 */
export async function getDashboardData(
  vehicle: VehicleOption = dashboardVehicle,
): Promise<DashboardData> {
  const [analysisResult, regionalResult, referenceResult] = await Promise.all([
    requestAnalysisValuation(vehicle),
    requestAnalysisRegionalMarket(),
    requestAnalysisReferences({
      make: vehicle.make,
      model: vehicle.model,
      year: vehicle.year,
    }),
  ]);

  const regionalMarket: RegionalMarketPoint[] =
    regionalResult.status === "ok"
      ? regionalResult.data.regions.map((point) => ({
          region: point.region,
          passengerCars: point.passenger_cars,
        }))
      : pocDashboardData.regionalMarket;

  const regionalSource: SourceDescriptor =
    regionalResult.status === "ok"
      ? {
          id: regionalResult.data.source,
          name: "Badan Pusat Statistik",
          type: "Official regional vehicle stock",
          confidence: "official",
          lastUpdated: `${regionalResult.data.year} table · latest persisted refresh`,
          note:
            "Passenger-car counts were fetched from the public BPS statistics table and persisted in Neon. They provide regional market-depth context, not a vehicle-price estimate.",
          url: regionalResult.data.source_url,
        }
      : bpsFallbackSource();

  const references: VehicleReferences =
    referenceResult.status === "ok"
      ? {
          njkb: toReferenceMatch(referenceResult.data.njkb),
          auctionLimit: toReferenceMatch(referenceResult.data.auction_limit),
        }
      : unavailableReferences();

  if (analysisResult.status !== "ok") {
    return {
      ...pocDashboardData,
      references: unavailableReferences(),
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
        detail: `${analysisResult.detail} The dashboard has returned to its clearly labelled default POC vehicle rather than showing unrelated numbers for your selection.`,
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

  const referencePoints: ValuePoint[] = [];
  if (references.njkb.status === "exact" && references.njkb.value !== undefined) {
    referencePoints.push({
      label: "Official NJKB reference",
      value: references.njkb.value,
      kind: "njkb",
      confidence: "official",
    });
  }
  if (
    references.auctionLimit.status === "exact" &&
    references.auctionLimit.value !== undefined
  ) {
    referencePoints.push({
      label: "Auction / downside reference",
      value: references.auctionLimit.value,
      kind: "auction_limit",
      confidence: "official",
    });
  }

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
    references,
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
      values: [listingSignal, ...referencePoints],
      priceHistory: [
        {
          date: "Current",
          value: result.valuation.estimate,
        },
      ],
    },
    sources: [regionalSource, analysisSource, ...referenceSources(references)],
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
