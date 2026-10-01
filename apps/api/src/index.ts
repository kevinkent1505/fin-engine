import { randomUUID } from "node:crypto";
import Fastify from "fastify";

import {
  AnalysisNotFoundError,
  requestVehicleValuation,
} from "./analysis-client";
import { vehicleValuationQuerySchema } from "./schema";

const app = Fastify({logger: true});

app.get("/health", async () => ({status: "ok", service: "api"}));

app.get("/v1/vehicles/valuation", async (request, reply) => {
  const parsed = vehicleValuationQuerySchema.safeParse(request.query);

  if (!parsed.success) {
    return reply.status(400).send({
      error: "invalid_request",
      details: parsed.error.flatten(),
    });
  }

  try {
    const data = await requestVehicleValuation(parsed.data);
    return {request_id: randomUUID(), data};
  } catch (error) {
    if (error instanceof AnalysisNotFoundError) {
      return reply.status(404).send({
        error: "no_comparables",
        message: error.message,
      });
    }

    request.log.error(error);
    return reply.status(502).send({
      error: "analysis_unavailable",
      message: "The analysis service could not complete the request.",
    });
  }
});

async function start() {
  await app.listen({
    port: Number(process.env.PORT ?? 8000),
    host: process.env.HOST ?? "0.0.0.0",
  });
}

start().catch((error) => {
  app.log.error(error);
  process.exit(1);
});
