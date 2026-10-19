#!/usr/bin/env node
/**
 * Cross-platform local commands for Fin Engine.
 *
 * Node >=20, Python >=3.12, Python's built-in venv and pip are sufficient.
 * No uv, shell activation, PowerShell, Bash, or Windows py launcher required.
 */
import { existsSync } from "node:fs";
import { spawn, spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const analysis = path.join(root, "apps", "analysis");
const venv = path.join(analysis, ".venv");
const onWindows = process.platform === "win32";
const venvPython = path.join(
  venv,
  ...(onWindows ? ["Scripts", "python.exe"] : ["bin", "python"]),
);

const defaultEnv = {
  ...process.env,
  ANALYSIS_BASE_URL: process.env.ANALYSIS_BASE_URL || "http://localhost:8001",
  VEHICLE_DATA_PATH:
    process.env.VEHICLE_DATA_PATH || path.join(root, "data", "sample", "vehicles.csv"),
};

function pythonVersion(command, prefix = []) {
  const result = spawnSync(
    command,
    [...prefix, "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"],
    { encoding: "utf8", windowsHide: true, timeout: 5000 },
  );
  if (result.status !== 0) return null;
  const match = result.stdout.trim().match(/^(\d+)\.(\d+)$/);
  if (!match) return null;
  const major = Number(match[1]);
  const minor = Number(match[2]);
  return major > 3 || (major === 3 && minor >= 12)
    ? result.stdout.trim()
    : null;
}

function pythonCandidates() {
  // An explicit override can be an absolute path with spaces. No shell needed.
  const override = process.env.FIN_ENGINE_PYTHON;
  if (override) return [{ command: override, prefix: [] }];

  const candidates = ["python3.12", "python3.13", "python3.14", "python3", "python"]
    .map((command) => ({ command, prefix: [] }));

  if (onWindows) {
    candidates.push(
      { command: "py", prefix: ["-3.12"] },
      { command: "py", prefix: ["-3.13"] },
      { command: "py", prefix: ["-3"] },
    );
    if (process.env.LOCALAPPDATA) {
      for (const version of ["Python312", "Python313", "Python314"]) {
        candidates.push({
          command: path.join(
            process.env.LOCALAPPDATA, "Programs", "Python", version, "python.exe",
          ),
          prefix: [],
        });
      }
    }
  }
  return candidates;
}

function findPython() {
  for (const candidate of pythonCandidates()) {
    const version = pythonVersion(candidate.command, candidate.prefix);
    if (version) return { ...candidate, version };
  }
  throw new Error(
    "Python 3.12+ not found. Install Python 3.12+ from python.org, " +
    "restart your terminal, then run 'yarn setup'. " +
    "Or set FIN_ENGINE_PYTHON to the full Python executable path.",
  );
}

function installedPython() {
  if (existsSync(venvPython) && pythonVersion(venvPython)) return venvPython;
  throw new Error(
    "Fin Engine's Python environment is missing or below Python 3.12. " +
    "Run 'yarn setup' first.",
  );
}

function run(command, args, options = {}) {
  return new Promise((resolve) => {
    const child = spawn(command, args, {
      stdio: "inherit",
      windowsHide: true,
      env: defaultEnv,
      ...options,
    });
    child.on("error", (error) => {
      console.error(`Could not start ${command}: ${error.message}`);
      resolve(1);
    });
    child.on("exit", (code) => resolve(code ?? 1));
  });
}

async function setup() {
  let python;
  if (existsSync(venvPython) && pythonVersion(venvPython)) {
    python = venvPython;
    console.log(`Using existing virtual environment: ${venv}`);
  } else {
    const interpreter = findPython();
    console.log(`Creating virtual environment with Python ${interpreter.version}`);
    const result = await run(
      interpreter.command,
      [...interpreter.prefix, "-m", "venv", venv],
      { cwd: analysis },
    );
    if (result !== 0) {
      throw new Error(
        "Could not create .venv. If it belongs to another operating system " +
        "or Python version, delete apps/analysis/.venv and retry.",
      );
    }
    python = installedPython();
  }

  let result = await run(python, ["-m", "pip", "install", "--upgrade", "pip"], {
    cwd: analysis,
  });
  if (result !== 0) return result;

  result = await run(python, ["-m", "pip", "install", "-e", ".[dev]"], {
    cwd: analysis,
  });
  if (result === 0) console.log("Python setup complete. Run 'yarn dev'.");
  return result;
}

async function pythonCommand(args) {
  return run(installedPython(), args, { cwd: analysis });
}

function yarnProcess(workspace, env) {
  const command = onWindows ? "cmd.exe" : "yarn";
  const args = onWindows
    ? ["/d", "/s", "/c", `yarn workspace ${workspace} dev`]
    : ["workspace", workspace, "dev"];
  return spawn(command, args, {
    cwd: root,
    env,
    stdio: "inherit",
    windowsHide: true,
    detached: !onWindows,
  });
}

function dev() {
  const python = installedPython();
  const children = [];
  let stopping = false;

  const stop = (code) => {
    if (stopping) return;
    stopping = true;
    for (const child of children) {
      if (!child.pid) continue;
      try {
        if (onWindows) {
          spawnSync("taskkill", ["/PID", String(child.pid), "/T", "/F"], {
            stdio: "ignore",
            windowsHide: true,
            timeout: 5000,
          });
        } else {
          process.kill(-child.pid, "SIGTERM");
        }
      } catch {
        // A child may have exited already.
      }
    }
    process.exit(code);
  };

  process.on("SIGINT", () => stop(130));
  process.on("SIGTERM", () => stop(143));

  const track = (name, child) => {
    children.push(child);
    child.on("error", (error) => {
      console.error(`${name} failed to start: ${error.message}`);
      stop(1);
    });
    child.on("exit", (code, signal) => {
      if (!stopping) {
        console.error(`${name} exited (code: ${code}, signal: ${signal}). Stopping services.`);
        stop(code || 1);
      }
    });
  };

  console.log("\nFin Engine local stack");
  console.log("  Dashboard  http://localhost:3000");
  console.log("  API        http://localhost:8000");
  console.log("  Analysis   http://localhost:8001");
  console.log("  Crawlers   not started\n");

  track(
    "Analysis",
    spawn(
      python,
      ["-m", "uvicorn", "riil_analysis.main:app", "--reload",
        "--host", "0.0.0.0", "--port", "8001"],
      {
        cwd: analysis,
        env: defaultEnv,
        stdio: "inherit",
        windowsHide: true,
        detached: !onWindows,
      },
    ),
  );
  track("API", yarnProcess("@fin-engine/api", defaultEnv));
  track("Dashboard", yarnProcess("@fin-engine/dashboard", defaultEnv));
}

async function main() {
  const [, , command, ...args] = process.argv;

  switch (command) {
    case "setup":
      return setup();
    case "dev":
      return dev();
    case "analysis":
      return pythonCommand([
        "-m", "uvicorn", "riil_analysis.main:app", "--reload",
        "--host", "0.0.0.0", "--port", "8001",
      ]);
    case "refresh-official":
      return pythonCommand(["-m", "riil_analysis.cli", "refresh-official"]);
    case "refresh-njkb":
      return pythonCommand([
        "-m", "riil_analysis.cli", "ingest",
        "--source", "njkb_latest", "--persist-db",
      ]);
    case "refresh-bps":
      return pythonCommand([
        "-m", "riil_analysis.cli", "ingest",
        "--source", "vehicle_stock_latest", "--persist-db",
      ]);
    case "ingest":
      return pythonCommand(["-m", "riil_analysis.cli", "ingest", ...args]);
    case "test":
      return pythonCommand(["-m", "pytest", ...args]);
    case "migrate":
      return pythonCommand(["-m", "alembic", ...args]);
    default:
      console.error(
        "Usage: node scripts/fin-engine.mjs " +
        "<setup|dev|analysis|refresh-official|refresh-njkb|refresh-bps|ingest|test|migrate>",
      );
      return 2;
  }
}

try {
  const result = await main();
  if (typeof result === "number") process.exitCode = result;
} catch (error) {
  console.error(error instanceof Error ? error.message : error);
  process.exitCode = 1;
}
