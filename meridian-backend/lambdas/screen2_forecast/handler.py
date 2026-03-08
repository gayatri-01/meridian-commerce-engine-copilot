import os
import sys
from datetime import datetime

CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
DATA_PATH = os.path.join(PROJECT_ROOT, "data")
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from shared.forecast_service import build_15_day_forecast
from shared.http_utils import parse_body, response


def lambda_handler(event, context):
    if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return response(200, {"ok": True})

    body = parse_body(event)
    default_anchor_date = datetime.utcnow().date().isoformat()
    anchor_date = body.get("anchor_date", default_anchor_date)
    try:
        parsed_date = datetime.strptime(anchor_date, "%Y-%m-%d")
    except ValueError:
        return response(400, {"error": "anchor_date must be in YYYY-MM-DD format."})

    try:
        result = build_15_day_forecast(base_path=DATA_PATH, anchor_date=parsed_date)
        return response(200, result)
    except Exception as exc:
        return response(500, {"error": str(exc), "source": "screen2_forecast"})
