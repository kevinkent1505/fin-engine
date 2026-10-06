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

export type VehicleOption = {
  make: string;
  model: string;
  year: number;
  region: string;
};

export type VehicleCatalog = {
  options: VehicleOption[];
  source:
    | "official"
    | "database"
    | "database_demo"
    | "database_mixed"
    | "development"
    | "fallback";
  detail: string;
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

export type AnalysisStatus = {
  state: "database" | "demo" | "development" | "fallback";
  method?: string;
  label: string;
  detail: string;
};

export type VehicleReferenceMatch = {
  status: "exact" | "range" | "unavailable";
  value?: number;
  low?: number;
  high?: number;
  candidateCount: number;
  variants: string[];
  sourceKeys: string[];
  sourceUrls: string[];
};

export type VehicleReferences = {
  njkb: VehicleReferenceMatch;
  auctionLimit: VehicleReferenceMatch;
};

export type DashboardData = {
  mode: "analysis" | "fallback";
  analysis: AnalysisStatus;
  snapshot: VehicleSnapshot;
  references: VehicleReferences;
  regionalMarket: RegionalMarketPoint[];
  sources: SourceDescriptor[];
};
