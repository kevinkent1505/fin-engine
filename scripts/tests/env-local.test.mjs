import assert from "node:assert/strict";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import { loadEnvLocal, parseEnvLocal } from "../env-local.mjs";

test("parses common dotenv values without evaluating shell syntax", () => {
  const parsed = parseEnvLocal([
    "# Local-only configuration",
    "DATABASE_URL=postgresql://demo:pa%23ss@host/neondb?sslmode=require",
    'ANALYSIS_BASE_URL="http://localhost:8001"',
    "export REGION=Indonesia",
    "WITH_COMMENT = value # ignored",
    "EMBEDDED_HASH=abc#def",
    "SINGLE_QUOTE='value # with spaces'",
    'QUOTED_ESCAPE="line\\nnext"',
    "EMPTY=",
    "COMMAND=$(echo should-not-run)",
  ].join("\r\n"));

  assert.equal(
    parsed.DATABASE_URL,
    "postgresql://demo:pa%23ss@host/neondb?sslmode=require",
  );
  assert.equal(parsed.ANALYSIS_BASE_URL, "http://localhost:8001");
  assert.equal(parsed.REGION, "Indonesia");
  assert.equal(parsed.WITH_COMMENT, "value");
  assert.equal(parsed.EMBEDDED_HASH, "abc#def");
  assert.equal(parsed.SINGLE_QUOTE, "value # with spaces");
  assert.equal(parsed.QUOTED_ESCAPE, "line\nnext");
  assert.equal(parsed.EMPTY, "");
  assert.equal(parsed.COMMAND, "$(echo should-not-run)");
});

test("loads root .env.local but respects existing environment variables", () => {
  const root = mkdtempSync(path.join(os.tmpdir(), "fin-engine-env-"));
  try {
    writeFileSync(
      path.join(root, ".env.local"),
      "\uFEFFDATABASE_URL='postgresql://local:password@localhost/db'\n" +
        "ANALYSIS_BASE_URL=http://localhost:8001\n",
    );
    const env = { DATABASE_URL: "postgresql://existing:pw@localhost/db" };
    assert.deepEqual(loadEnvLocal({ root, env }), { found: true, applied: 1 });
    assert.equal(env.DATABASE_URL, "postgresql://existing:pw@localhost/db");
    assert.equal(env.ANALYSIS_BASE_URL, "http://localhost:8001");
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("missing file does not change environment", () => {
  const root = mkdtempSync(path.join(os.tmpdir(), "fin-engine-env-"));
  try {
    const env = { KEEP: "existing" };
    assert.deepEqual(loadEnvLocal({ root, env }), { found: false, applied: 0 });
    assert.deepEqual(env, { KEEP: "existing" });
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("malformed env file fails before changing any values", () => {
  const root = mkdtempSync(path.join(os.tmpdir(), "fin-engine-env-"));
  try {
    writeFileSync(
      path.join(root, ".env.local"),
      "DATABASE_URL=postgresql://example/db\nbroken line\n",
    );
    const env = {};
    assert.throws(
      () => loadEnvLocal({ root, env }),
      /Invalid .env.local syntax at line 2/,
    );
    assert.deepEqual(env, {});
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test("rejects unclosed quotes without printing secret values", () => {
  assert.throws(
    () => parseEnvLocal('DATABASE_URL="secret'),
    /Invalid quoted value in .env.local at line 1/,
  );
});
