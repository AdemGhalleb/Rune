#!/usr/bin/env node
/**
 * Run backend and frontend dev servers together.
 */

import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

function run(label, command, args, cwd) {
  const child = spawn(command, args, {
    cwd,
    stdio: "inherit",
    shell: process.platform === "win32",
    env: process.env,
  });

  child.on("exit", (code) => {
    if (code && code !== 0) {
      console.error(`[${label}] exited with code ${code}`);
      process.exit(code);
    }
  });

  return child;
}

const backend = run("backend", "node", [path.join(root, "scripts", "run-backend.js")], root);
const frontend = run("frontend", "npm", ["run", "dev", "--workspace=@rune/desktop"], root);

function shutdown() {
  backend.kill("SIGINT");
  frontend.kill("SIGINT");
}

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
