#!/usr/bin/env bash
# Start the SVM web app: backend on port 8000 and frontend on port 5173. Ctrl+C stops both.
# (The GAN project's app uses the same ports: do not run both at once.)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
[ -x .venv/bin/python ] || { echo "Environment missing. Run: python3 -m venv .venv && .venv/bin/pip install -r svm_variant/requirements.txt"; exit 1; }
[ -d svm_variant/webapp/frontend/node_modules ] || { echo "Frontend deps missing. Run: (cd svm_variant/webapp/frontend && npm install)"; exit 1; }
[ -f outputs/svm_variant/model/svm_model.joblib ] || { echo "Trained model missing. Run: .venv/bin/python svm_variant/train_select.py && .venv/bin/python svm_variant/evaluate_test.py"; exit 1; }
if lsof -iTCP:8000 -sTCP:LISTEN >/dev/null 2>&1 || lsof -iTCP:5173 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Port 8000 or 5173 is already in use. Stop the other process first."; exit 1
fi
.venv/bin/python -m uvicorn svm_variant.webapp.backend.main:app --host 127.0.0.1 --port 8000 &
BACK=$!
(cd svm_variant/webapp/frontend && npm run dev) &
FRONT=$!
trap 'kill $BACK $FRONT 2>/dev/null || true' EXIT INT TERM
echo "Backend: http://127.0.0.1:8000/docs   Frontend: http://localhost:5173"
wait
