#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "==> Setting up Rune backend..."
cd "$ROOT/apps/backend"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "==> Installing frontend dependencies..."
cd "$ROOT"
npm install

echo ""
echo "Setup complete."
echo "  Backend:  npm run dev:backend"
echo "  Frontend: npm run dev"
echo "  Both:     npm run dev:all"
