export type DataConfidence = "official" | "observed" | "illustrative";

export type SourceDescriptor = {
  id: string;
  name: string;
  type: string;
  confidence: DataConfidence;
  lastUpdated: string;
  note: string;
  url?: string;
};

export type Metric = {
  label: string;
  value: string;
  helper?: string;
  tone?: "default" | "positive" | "warning";
};

export type ValuePoint = {
  label: string;
  value: number;
  kind: "listing" | "njkb" | "auction_limit";
  confidence: DataConfidence;
};

export type HistoricalPricePoint = {
  date: string;
  value: number;
};

export type RegionalMarketPoint = {
  region: string;
  passengerCars: number;
  marketMedian?: number;
};

export type VehicleSnapshot = {
  make: string;
  model: string;
  year: number;
  region: string;
  variant: string;
  sampleSize: number;
  values: ValuePoint[];
  priceHistory: HistoricalPricePoint[];
  observedRange: [number, number];
  lastRefresh: string;
};

export type DashboardData = {
  mode: "poc";
  snapshot: VehicleSnapshot;
  regionalMarket: RegionalMarketPoint[];
  sources: SourceDescriptor[];
};
