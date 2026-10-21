/**
 * Fin Engine's no-dependency .env.local reader.
 *
 * Local settings are project-scoped. Existing shell/CI environment variables
 * always win. Values are parsed as data: no shell execution or interpolation.
 */
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

export function parseEnvLocal(source) {
  const values = {};
  const lines = source.replace(/^\uFEFF/, "").split(/\r?\n/);

  for (const [index, originalLine] of lines.entries()) {
    const line = originalLine.trim();
    if (!line || line.startsWith("#")) continue;

    const match = /^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$/.exec(line);
    if (!match) {
      throw new Error(
        `Invalid .env.local syntax at line ${index + 1}: expected KEY=VALUE.`,
      );
    }

    const [, key, remainder] = match;
    let value;

    if (remainder.startsWith('"') || remainder.startsWith("'")) {
      const quote = remainder[0];
      let end = -1;

      for (let i = 1; i < remainder.length; i += 1) {
        if (remainder[i] === quote && remainder[i - 1] !== "\\") {
          end = i;
          break;
        }
      }

      const trailing = end < 0 ? "" : remainder.slice(end + 1).trim();
      if (end < 0 || (trailing && !trailing.startsWith("#"))) {
        throw new Error(
          `Invalid quoted value in .env.local at line ${index + 1}.`,
        );
      }

      value = remainder.slice(1, end);
      if (quote === '"') {
        value = value.replace(/\\(n|r|t|"|\\)/g, (_, escaped) => {
          return { n: "\n", r: "\r", t: "\t", '"': '"', "\\": "\\" }[escaped];
        });
      }
    } else {
      // A # after whitespace starts a comment; embedded # is part of the
      // value. For passwords with spaces or comments, quote the full URL.
      value = remainder.replace(/\s+#.*$/, "").trim();
    }

    values[key] = value;
  }

  return values;
}

export function loadEnvLocal({ root, env = process.env } = {}) {
  if (!root) throw new TypeError("loadEnvLocal requires a repository root");
  const filePath = path.join(root, ".env.local");

  if (!existsSync(filePath)) return { found: false, applied: 0 };

  // Parse the entire file before assigning anything, so malformed files cannot
  // leave a partially applied configuration in memory.
  const values = parseEnvLocal(readFileSync(filePath, "utf8"));
  let applied = 0;
  for (const [key, value] of Object.entries(values)) {
    if (Object.hasOwn(env, key)) continue;
    env[key] = value;
    applied += 1;
  }
  return { found: true, applied };
}
