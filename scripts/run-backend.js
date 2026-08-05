#!/usr/bin/env node
/**
 * Start the FastAPI backend for local development.
 * Works cross-platform without requiring a global Python install path.
 */

import { spawn } from "node:child_process";
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

const child = spawn(python, ["-m", "uvicorn", "app.main:create_app", "--factory", "--host", "127.0.0.1", "--port", "18742", "--reload"], {
  cwd: backendDir,
  stdio: "inherit",
  env: {
    ...process.env,
    PYTHONPATH: backendDir,
  },
});

child.on("exit", (code) => process.exit(code ?? 1));

process.on("SIGINT", () => child.kill("SIGINT"));
process.on("SIGTERM", () => child.kill("SIGTERM"));
