#!/usr/bin/env bash
rc=0
python3 -c "import json;json.load(open('findings.json'))" 2>/dev/null && echo "- ✅ findings.json is valid JSON" || { echo "- ❌ findings.json is not valid JSON"; rc=1; }
grep -q 'TODO' findings.json && { echo "- ❌ findings.json still has TODO"; rc=1; } || echo "- ✅ findings.json has no TODO"
grep -qi 'USER' Dockerfile.fixed && grep -q 'FROM' Dockerfile.fixed && echo "- ✅ Dockerfile.fixed is written" || { echo "- ❌ Dockerfile.fixed is not written"; rc=1; }
grep -rqE 'ghp_[0-9a-f]{32}' . --exclude-dir=.git --exclude=SUBMISSION.md --exclude=findings.json && { echo "- ❌ the token is committed outside findings.json"; rc=1; } || echo "- ✅ the token is not committed in files"
grep -qE '^ALL CHECKS PASSED \(' SUBMISSION.md && echo "- ✅ SUBMISSION.md shows ALL CHECKS PASSED" || { echo "- ❌ paste the verify.sh output ('ALL CHECKS PASSED') into SUBMISSION.md"; rc=1; }
exit $rc
