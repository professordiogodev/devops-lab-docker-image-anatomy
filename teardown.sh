#!/usr/bin/env bash
# Removes the lab's containers, images and files. Run with: ./teardown.sh
set -u
cd "$(dirname "$0")"
docker ps -aq --filter ancestor=legacy-pollie:1 --filter ancestor=pollie-fixed:1 | xargs -r docker rm -f >/dev/null 2>&1
docker rm -f anatomy-check >/dev/null 2>&1
docker image rm legacy-pollie:1 pollie-fixed:1 >/dev/null 2>&1 && echo "removed the images"
rm -rf pollie secrets work .lab/.truth.json
echo "Now run ./verify-teardown.sh"
