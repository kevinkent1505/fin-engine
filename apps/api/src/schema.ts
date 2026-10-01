import { z } from "zod";

export const vehicleValuationQuerySchema = z.object({
  make: z.string().trim().min(1).max(80),
  model: z.string().trim().min(1).max(80),
  year: z.coerce.number().int().min(1900).max(2100),
  region: z.string().trim().min(1).max(120),
});

export type VehicleValuationQuery = z.infer<typeof vehicleValuationQuerySchema>;

export const analysisValuationResponseSchema = z.object({
  vehicle: z.object({
    make: z.string(),
    model: z.string(),
    year: z.number().int(),
  }),
  region: z.string(),
  valuation: z.object({
    estimate: z.number().int().nonnegative(),
    low: z.number().int().nonnegative(),
    high: z.number().int().nonnegative(),
  }),
  sample_size: z.number().int().positive(),
  method: z.string(),
});

export type AnalysisValuationResponse = z.infer<typeof analysisValuationResponseSchema>;
