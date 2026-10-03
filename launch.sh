#!/usr/bin/env bash
# Create the virtual environment with uv and launch the agent.
# Usage: ./launch.sh  (from any folder)
set -euo pipefail

cd "$(dirname "$0")"

if ! command -v uv >/dev/null 2>&1; then
    echo "uv is not installed: https://docs.astral.sh/uv/" >&2
    exit 1
fi

if [ ! -f .env ]; then
    echo "Missing .env file: add MISTRAL_API_KEY=<your key>" >&2
    exit 1
fi

# Create .venv with Python 3.12 or later, then install the locked
# dependencies of pyproject.toml and uv.lock.
uv venv --allow-existing --python ">=3.12" .venv
uv sync --frozen

# shellcheck disable=SC1091
source .venv/bin/activate
python main.py
