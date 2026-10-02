import type { VehicleOption } from "@/lib/types";

type AnalysisValuationResponse = {
  vehicle: {
    make: string;
    model: string;
    year: number;
  };
  region: string;
  valuation: {
    estimate: number;
    low: number;
    high: number;
  };
  sample_size: number;
  method: string;
};

type AnalysisVehicleCatalogResponse = {
  vehicles: VehicleOption[];
  source: "database" | "development";
};

export type AnalysisValuationResult =
  | {
      status: "ok";
      data: AnalysisValuationResponse;
    }
  | {
      status: "not_found" | "unavailable";
      detail: string;
    };

export type AnalysisVehicleCatalogResult =
  | {
      status: "ok";
      data: AnalysisVehicleCatalogResponse;
    }
  | {
      status: "unavailable";
      detail: string;
    };

const analysisBaseUrl =
  process.env.ANALYSIS_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8001";

export async function requestAnalysisVehicleOptions(): Promise<AnalysisVehicleCatalogResult> {
  try {
    const response = await fetch(`${analysisBaseUrl}/internal/v1/vehicles/options`, {
      cache: "no-store",
      signal: AbortSignal.timeout(4_000),
    });

    if (!response.ok) {
      return {
        status: "unavailable",
        detail: `The analysis engine returned HTTP ${response.status} while loading vehicle choices.`,
      };
    }

    return {
      status: "ok",
      data: (await response.json()) as AnalysisVehicleCatalogResponse,
    };
  } catch (error) {
    const detail =
      error instanceof Error
        ? `Vehicle choices could not be loaded from the analysis engine: ${error.message}`
        : "Vehicle choices could not be loaded from the analysis engine.";

    return {
      status: "unavailable",
      detail,
    };
  }
}

export async function requestAnalysisValuation(input: {
  make: string;
  model: string;
  year: number;
  region: string;
}): Promise<AnalysisValuationResult> {
  try {
    const response = await fetch(
      `${analysisBaseUrl}/internal/v1/vehicles/valuation`,
      {
        method: "POST",
        headers: {
          "content-type": "application/json",
        },
        body: JSON.stringify(input),
        cache: "no-store",
        signal: AbortSignal.timeout(4_000),
      },
    );

    if (response.status === 404) {
      return {
        status: "not_found",
        detail: "The analysis engine is reachable but has no comparable observations for the selected vehicle.",
      };
    }

    if (!response.ok) {
      return {
        status: "unavailable",
        detail: `The analysis engine returned HTTP ${response.status}.`,
      };
    }

    return {
      status: "ok",
      data: (await response.json()) as AnalysisValuationResponse,
    };
  } catch (error) {
    const detail =
      error instanceof Error
        ? `The analysis engine could not be reached: ${error.message}`
        : "The analysis engine could not be reached.";

    return {
      status: "unavailable",
      detail,
    };
  }
}
