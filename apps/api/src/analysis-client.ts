import {
  analysisValuationResponseSchema,
  type AnalysisValuationResponse,
  type VehicleValuationQuery,
} from "./schema";

export class AnalysisNotFoundError extends Error {}

export async function requestVehicleValuation(
  input: VehicleValuationQuery,
): Promise<AnalysisValuationResponse> {
  const baseUrl = process.env.ANALYSIS_BASE_URL ?? "http://localhost:8001";

  const response = await fetch(`${baseUrl}/internal/v1/vehicles/valuation`, {
    method: "POST",
    headers: {"content-type": "application/json"},
    body: JSON.stringify(input),
  });

  if (response.status === 404) {
    throw new AnalysisNotFoundError("No comparable vehicle observations were found.");
  }

  if (!response.ok) {
    throw new Error(`Analysis service returned HTTP ${response.status}.`);
  }

  return analysisValuationResponseSchema.parse(await response.json());
}
