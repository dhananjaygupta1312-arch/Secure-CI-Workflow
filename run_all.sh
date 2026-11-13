#!/usr/bin/env bash
# Usage: ./run_all.sh [output-folder]
OUT=${1:-evidence/latest}
mkdir -p "$OUT"
FAIL=0

echo "=== 1/5 TESTS ===";   pytest -v --junitxml="$OUT/test-results.xml" || FAIL=1
echo "=== 2/5 SAST ===";    semgrep scan --config auto --error --json-output="$OUT/semgrep.json" app/ || FAIL=1
echo "=== 3/5 SCA ===";     pip-audit -r app/requirements.txt -f json -o "$OUT/pip-audit.json" || FAIL=1
echo "=== 4/5 SECRETS ==="; gitleaks detect --source . --report-format json --report-path "$OUT/gitleaks.json" || FAIL=1
echo "=== 5/5 SBOM ===";    cyclonedx-py requirements app/requirements.txt -o "$OUT/sbom.json"

if [ $FAIL -eq 0 ]; then echo "RESULT: PASS (all checks clean)"; else echo "RESULT: FAIL (findings above)"; fi
exit $FAIL
