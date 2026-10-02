import { requestAnalysisValuation } from "@/lib/data/analysis";
import { pocDashboardData } from "@/lib/data/poc";
import type { DashboardData, SourceDescriptor, ValuePoint } from "@/lib/types";

const dashboardVehicle = {
  make: process.env.DASHBOARD_VEHICLE_MAKE ?? "Toyota",
  model: process.env.DASHBOARD_VEHICLE_MODEL ?? "Avanza",
  year: Number(process.env.DASHBOARD_VEHICLE_YEAR ?? "2025"),
  region: process.env.DASHBOARD_VEHICLE_REGION ?? "DKI Jakarta",
};

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
export async function getDashboardData(): Promise<DashboardData> {
  const analysisResult = await requestAnalysisValuation(dashboardVehicle);

  if (analysisResult.status !== "ok") {
    return {
      ...pocDashboardData,
      analysis: {
        state: "fallback",
        label: "Fallback POC data",
        detail: analysisResult.detail,
      },
    };
  }

  const result = analysisResult.data;
  const databaseBacked = result.method === "comparable_market_db_v1";
  const confidence = databaseBacked ? "observed" : "illustrative";

  const listingSignal: ValuePoint = {
    label: databaseBacked
      ? "Analysis-engine asking median"
      : "Development comparable median",
    value: result.valuation.estimate,
    kind: "listing",
    confidence,
  };

  const otherSignals = pocDashboardData.snapshot.values.filter(
    (item) => item.kind !== "listing",
  );

  const analysisSource: SourceDescriptor = {
    id: "fin_engine_analysis",
    name: "Fin Engine analysis engine",
    type: databaseBacked
      ? "Neon-backed marketplace comparable valuation"
      : "Development comparable valuation",
    confidence,
    lastUpdated: "Current dashboard request",
    note: databaseBacked
      ? "Median and range are calculated from the latest persisted listing observation per stable marketplace record, avoiding repeated-crawl overweighting."
      : "The dashboard is connected to the Python analysis service, but that service is currently using the committed development comparable CSV because DATABASE_URL is not configured there.",
  };

  return {
    ...pocDashboardData,
    mode: "analysis",
    analysis: {
      state: databaseBacked ? "database" : "development",
      method: result.method,
      label: databaseBacked
        ? "Analysis engine · Neon observations"
        : "Analysis engine · development comparables",
      detail: databaseBacked
        ? `${result.sample_size} latest marketplace listing observations are feeding the valuation snapshot.`
        : `${result.sample_size} development comparable rows are feeding the valuation snapshot. Connect the analysis service to Neon for observed marketplace data.`,
    },
    snapshot: {
      ...pocDashboardData.snapshot,
      make: result.vehicle.make,
      model: result.vehicle.model,
      year: result.vehicle.year,
      region: result.region,
      sampleSize: result.sample_size,
      observedRange: [result.valuation.low, result.valuation.high],
      lastRefresh: databaseBacked
        ? "Analysis engine · Neon"
        : "Analysis engine · development CSV",
      values: [listingSignal, ...otherSignals],
      priceHistory: [
        {
          date: "Current",
          value: result.valuation.estimate,
        },
      ],
    },
    sources: [
      ...pocDashboardData.sources.filter(
        (source) => source.id !== "marketplace_poc",
      ),
      analysisSource,
    ],
  };
}

export async function getVehicleSnapshot() {
  const data = await getDashboardData();
  return data.snapshot;
}

export async function getRegionalMarket() {
  const data = await getDashboardData();
  return data.regionalMarket;
}

export async function getSources() {
  const data = await getDashboardData();
  return data.sources;
}
