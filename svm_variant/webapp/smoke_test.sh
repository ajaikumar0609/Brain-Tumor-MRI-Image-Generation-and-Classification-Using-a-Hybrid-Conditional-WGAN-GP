#!/usr/bin/env bash
# Integration smoke test against a RUNNING stack (./svm_variant/webapp/run_dev.sh). Goes through the Vite proxy on 5173, like the browser does.
set -uo pipefail
B=${1:-http://localhost:5173}; fail=0
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
chk() { if eval "$2" >/dev/null 2>&1; then echo "PASS $1"; else echo "FAIL $1"; fail=1; fi; }
IMG=$(ls "$ROOT"/archive/Testing/glioma/*.jpg | head -1)
chk "frontend serves the page"          "curl -sf $B/ | grep -q 'Brain MRI SVM'"
chk "proxy -> /api/health"              "curl -sf $B/api/health | grep -q '\"ok\"'"
chk "SVM model available and matches the evaluated model" "curl -sf $B/api/models/status | python3 -c 'import json,sys;d=json.load(sys.stdin);assert d[\"classifier\"][\"available\"] and d[\"classifier\"][\"matches_evaluated_model\"]'"
chk "metrics equal the saved test file" "curl -sf $B/api/metrics | python3 -c 'import json,sys;d=json.load(sys.stdin);t=json.load(open(\"$ROOT/outputs/svm_variant/test/test_evaluation.json\"));assert d[\"accuracy\"]==t[\"accuracy\"] and d[\"macro_f1\"]==t[\"macro_f1\"]'"
chk "classify a real image (SVM output)" "curl -sf -F file=@$IMG $B/api/classify | python3 -c 'import json,sys;d=json.load(sys.stdin);assert d[\"predicted_class\"] in [\"glioma\",\"meningioma\",\"notumor\",\"pituitary\"] and len(d[\"decision_scores\"])==4'"
chk "classify rejects a text file"      "curl -s -F file=@/etc/hosts $B/api/classify | grep -q not_an_image"
chk "no generator endpoint exists"      "[ \$(curl -s -o /dev/null -w '%{http_code}' -X POST $B/api/generate) = 404 ]"
exit $fail
