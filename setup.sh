#!/usr/bin/env bash
# Clones Pollie, plants a secret and builds the legacy image. Run: ./setup.sh
set -u
cd "$(dirname "$0")"
for c in docker git python3; do command -v "$c" >/dev/null || { echo "MISSING: $c"; exit 1; }; done
docker info >/dev/null 2>&1 || { echo "Docker is not running."; exit 1; }
[ -d pollie ] || git clone -q -c advice.detachedHead=false --depth 1 --branch v0.1.1 https://github.com/professordiogodev/pollie.git pollie || { echo "could not clone pollie"; exit 1; }
mkdir -p secrets
TOKEN="ghp_$(python3 -c 'import secrets;print(secrets.token_hex(16))')"
printf 'REGISTRY_TOKEN=%s\n' "$TOKEN" > secrets/registry.env
printf '{"token": "%s"}\n' "$TOKEN" > .lab/.truth.json
echo "Building the legacy image (a few minutes: it is big)..."
docker build -q -f Dockerfile.legacy -t legacy-pollie:1 . >/dev/null || { echo "build failed"; exit 1; }
docker images legacy-pollie:1 --format "Built legacy-pollie:1  size {{.Size}}"
echo "Start your investigation:  docker history --no-trunc legacy-pollie:1"
