import { pocDashboardData } from "@/lib/data/poc";
import type { DashboardData } from "@/lib/types";

/**
 * Server-side data access boundary for dashboard pages.
 *
 * POC: returns deterministic public-reference/demo fixtures.
 * Next: replace internals with TypeScript API/Neon-backed queries without
 * changing route components.
 */
export async function getDashboardData(): Promise<DashboardData> {
  return pocDashboardData;
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
