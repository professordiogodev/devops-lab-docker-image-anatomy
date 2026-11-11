#!/usr/bin/env bash
# Proves the lab left nothing on your machine. Run with: ./verify-teardown.sh
set -u
cd "$(dirname "$0")"
pass=0; failn=0
check() { local d="$1"; shift; if "$@" >/dev/null 2>&1; then echo "PASS  $d"; pass=$((pass+1)); else echo "FAIL  $d"; failn=$((failn+1)); fi; }
check "the image legacy-pollie:1 is gone" bash -c '! docker image inspect legacy-pollie:1'
check "the image pollie-fixed:1 is gone" bash -c '! docker image inspect pollie-fixed:1'
check "no container of the lab is left" bash -c '[ -z "$(docker ps -aq --filter name=anatomy-check)" ]'
check "the planted secret and the cloned source are gone" bash -c '[ ! -d secrets ] && [ ! -d pollie ]'
echo
if [ "$failn" -eq 0 ]; then echo "TEARDOWN VERIFIED ($pass/$pass) on this machine"; else echo "NOT CLEAN: $failn leftover(s). Remove them and run this again."; fi
exit "$failn"
