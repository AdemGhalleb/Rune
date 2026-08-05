#!/usr/bin/env node
/**
 * Run backend pytest suite.
 */

import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const backendDir = path.join(root, "apps", "backend");

const venvPython =
  process.platform === "win32"
    ? path.join(backendDir, ".venv", "Scripts", "python.exe")
    : path.join(backendDir, ".venv", "bin", "python");

const python = existsSync(venvPython) ? venvPython : process.platform === "win32" ? "python" : "python3";

const result = spawnSync(python, ["-m", "pytest"], {
  cwd: backendDir,
  stdio: "inherit",
  env: {
    ...process.env,
    PYTHONPATH: backendDir,
  },
});

process.exit(result.status ?? 1);
