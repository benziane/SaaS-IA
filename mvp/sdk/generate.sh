#!/bin/bash
# ===========================================================================
# SaaS-IA SDK — OpenAPI schema fetcher
#
# Fetches the live OpenAPI schema from the running backend and saves it
# alongside the hand-crafted SDKs for reference.
#
# Usage:
#   ./mvp/sdk/generate.sh                       # default localhost:8004
#   BASE_URL=https://api.saas-ia.com ./mvp/sdk/generate.sh
# ===========================================================================

set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8004}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT="$SCRIPT_DIR/openapi.json"

echo "Fetching OpenAPI schema from $BASE_URL/openapi.json ..."
if curl -sf "$BASE_URL/openapi.json" -o "$OUTPUT"; then
    echo "Schema saved to $OUTPUT"
    echo ""
    echo "Endpoints found: $(python3 -c "
import json, sys
with open('$OUTPUT') as f:
    spec = json.load(f)
print(sum(len(methods) for methods in spec.get('paths', {}).values()))
" 2>/dev/null || echo 'N/A')"
else
    echo "ERROR: Could not reach $BASE_URL/openapi.json"
    echo "Make sure the backend is running (cd mvp && docker compose up -d)"
    exit 1
fi

echo ""
echo "SDKs are hand-crafted — update manually if endpoints change."
echo ""
echo "  TypeScript:  $SCRIPT_DIR/typescript/src/"
echo "  Python:      $SCRIPT_DIR/python/saas_ia/"
