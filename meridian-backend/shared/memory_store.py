import os
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key


class DynamoMemoryStore:
    def __init__(self, table_name: Optional[str] = None, region: Optional[str] = None) -> None:
        self.table_name = table_name or os.getenv("MEMORY_TABLE_NAME", "MeridianAgentMemory")
        session = boto3.session.Session(region_name=region or os.getenv("AWS_REGION", "us-east-1"))
        self.table = session.resource("dynamodb").Table(self.table_name)

    def store(self, session_id: str, tags: List[str], insight: str) -> None:
        item = {
            "session_id": session_id,
            "ts": datetime.utcnow().isoformat(),
            "tags": tags,
            "insight": insight,
        }
        self.table.put_item(Item=item)

    def fetch_recent(self, session_id: str) -> Dict[str, Any]:
        try:
            result = self.table.query(
                KeyConditionExpression=Key("session_id").eq(session_id),
                ScanIndexForward=False,
                Limit=1,
            )
            items = result.get("Items", [])
            if not items:
                return {"message": "No memory found."}
            return {"past_insight": items[0].get("insight", "")}
        except ClientError as exc:
            return {"error": f"DynamoDB error: {exc.response.get('Error', {}).get('Message', str(exc))}"}


def safe_json_extract_array(raw_text: str) -> List[Dict[str, Any]]:
    import re

    if not raw_text:
        return []

    match = re.search(r"\[\s*\{.*\}\s*\]", raw_text, re.DOTALL)
    if not match:
        return []
    try:
        value = json.loads(match.group(0))
        if isinstance(value, list):
            return value
    except json.JSONDecodeError:
        return []
    return []
