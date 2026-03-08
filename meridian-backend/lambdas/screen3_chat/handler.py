import os
import sys

CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from shared.chat_service import chat_with_kb
from shared.http_utils import parse_body, response


def lambda_handler(event, context):
    if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return response(200, {"ok": True})

    body = parse_body(event)
    question = body.get("question", "What is the reorder plan for high-moving milk SKUs?")
    session_id = body.get("session_id", "chat-default-session")
    history = body.get("history", [])
    if not isinstance(history, list):
        history = []

    try:
        result = chat_with_kb(question=question, session_id=session_id, chat_history=history)
        if result.get("error"):
            return response(500, result)
        return response(200, result)
    except Exception as exc:
        return response(500, {"error": str(exc), "source": "screen3_chat"})
