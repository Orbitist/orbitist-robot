#!/usr/bin/env bash
# One-time setup for the Orbitist simulator: Python environment + ArduPilot Rover 4.6.3 SITL.
# Tested on macOS (Apple silicon, Xcode command-line tools). Linux works the same way.
# Takes ~10 minutes, mostly downloading and compiling ArduPilot.
set -euo pipefail
cd "$(dirname "$0")"

AP_TAG="Rover-4.6.3"

if ! command -v uv >/dev/null; then
    echo "Install uv first: https://docs.astral.sh/uv/  (or create .venv with python3.12 -m venv)" >&2
    exit 1
fi

uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt

if [ ! -d ardupilot ]; then
    git clone --depth 1 --branch "$AP_TAG" https://github.com/ArduPilot/ardupilot.git ardupilot
    (cd ardupilot && git submodule update --init --recursive --depth 1)
fi

# Call waf with the venv's Python explicitly: ArduPilot's build checks for empy/pexpect/
# pkg_resources in whichever interpreter runs waf.
(cd ardupilot && ../.venv/bin/python ./waf configure --board sitl && ../.venv/bin/python ./waf rover)

echo
echo "Done. Try:"
echo "  .venv/bin/python coverage.py lawns/sample-farm.json"
echo "  .venv/bin/python run_sitl.py"
