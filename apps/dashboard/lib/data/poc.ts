import type { DashboardData } from "@/lib/types";

/**
 * Fallback/reference data used only when the Python analysis service cannot
 * provide a valuation snapshot.
 *
 * Official/public-reference values are explicitly marked `official`.
 * Marketplace and auction figures below are illustrative and must remain
 * visibly labelled as such.
 *
 * BPS values are from the public 2023 provincial motor-vehicle table.
 * The NJKB value is from Permendagri No. 7 Tahun 2025 for Toyota Avanza
 * 1.5 Veloz M/T, production year 2025.
 */
export const pocDashboardData: DashboardData = {
  mode: "fallback",
  analysis: {
    state: "fallback",
    label: "Fallback POC data",
    detail: "The analysis engine did not return a usable valuation. Illustrative market fixtures are being shown instead.",
  },
  snapshot: {
    make: "Toyota",
    model: "Avanza",
    year: 2025,
    region: "DKI Jakarta",
    variant: "1.5 Veloz M/T",
    sampleSize: 42,
    observedRange: [205_000_000, 252_000_000],
    lastRefresh: "Fallback POC fixture",
    values: [
      {
        label: "Indicative asking median",
        value: 232_000_000,
        kind: "listing",
        confidence: "illustrative",
      },
      {
        label: "NJKB reference",
        value: 214_000_000,
        kind: "njkb",
        confidence: "official",
      },
      {
        label: "Auction / downside reference",
        value: 188_000_000,
        kind: "auction_limit",
        confidence: "illustrative",
      },
    ],
    priceHistory: [
      { date: "May", value: 241_000_000 },
      { date: "Jun", value: 239_000_000 },
      { date: "Jul", value: 237_000_000 },
      { date: "Aug", value: 235_000_000 },
      { date: "Sep", value: 233_000_000 },
      { date: "Oct", value: 232_000_000 },
    ],
  },
  regionalMarket: [
    { region: "Jawa Timur", passengerCars: 5_439_502, marketMedian: 225_000_000 },
    { region: "Jawa Barat", passengerCars: 2_819_163, marketMedian: 228_000_000 },
    { region: "DKI Jakarta", passengerCars: 2_272_301, marketMedian: 232_000_000 },
    { region: "Jawa Tengah", passengerCars: 1_627_049, marketMedian: 221_000_000 },
    { region: "Banten", passengerCars: 1_005_073, marketMedian: 229_000_000 },
    { region: "Sumatera Utara", passengerCars: 872_015, marketMedian: 218_000_000 },
    { region: "Bali", passengerCars: 522_639, marketMedian: 234_000_000 },
  ],
  sources: [
    {
      id: "bps_vehicle_stock_2023",
      name: "Badan Pusat Statistik",
      type: "Regional vehicle stock",
      confidence: "official",
      lastUpdated: "2023 table",
      note: "Passenger-car counts by province used for regional market context.",
      url: "https://www.bps.go.id/id/statistics-table/3/VjJ3NGRGa3dkRk5MTlU1bVNFOTVVbmQyVURSTVFUMDkjMw%3D%3D/jumlah-kendaraan-bermotor-menurut-provinsi-dan-jenis-kendaraan",
    },
    {
      id: "kemendagri_njkb_2025",
      name: "Kementerian Dalam Negeri / JDIH BPK",
      type: "NJKB official reference",
      confidence: "official",
      lastUpdated: "Permendagri No. 7 Tahun 2025",
      note: "Toyota Avanza 1.5 Veloz M/T 2025 NJKB reference used in the POC.",
      url: "https://peraturan.bpk.go.id/Details/321612/permendagri-no-7-tahun-2025",
    },
    {
      id: "marketplace_poc",
      name: "Marketplace observations",
      type: "Asking-price signal",
      confidence: "illustrative",
      lastUpdated: "Fallback fixture",
      note: "Fallback only. The primary dashboard path now requests valuation output from the Fin Engine analysis service.",
    },
    {
      id: "auction_poc",
      name: "Government auction observations",
      type: "Downside / auction-limit signal",
      confidence: "illustrative",
      lastUpdated: "POC fixture",
      note: "UI placeholder until persisted government auction history is exposed through the analysis layer.",
    },
  ],
};
