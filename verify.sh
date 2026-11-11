#!/usr/bin/env bash
# Checks your findings and builds and inspects your fixed image. Run with: ./verify.sh
cd "$(dirname "$0")" || exit 1
docker image inspect legacy-pollie:1 >/dev/null 2>&1 || { echo "Run ./setup.sh first." >&2; exit 1; }
exec python3 .lab/anatomycheck.py
