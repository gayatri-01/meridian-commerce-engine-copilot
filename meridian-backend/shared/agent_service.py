import json
import os
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Tuple

import boto3
import pandas as pd
import requests

from .memory_store import DynamoMemoryStore, safe_json_extract_array


def sanitize_for_bedrock(data: Any) -> Any:
    if isinstance(data, dict):
        return {k: sanitize_for_bedrock(v) for k, v in data.items()}
    if isinstance(data, list):
        return [sanitize_for_bedrock(v) for v in data]
    if hasattr(data, "isoformat"):
        return data.isoformat()
    if isinstance(data, (datetime, pd.Timestamp)):
        return str(data)
    return data


class HyperlocalIntelligence:
    def __init__(self, base_path: str, anchor_date: datetime):
        self.base_path = base_path
        self.today = anchor_date
        self.city = os.getenv("CITY_NAME", "Dombivli")
        self.default_lat = float(os.getenv("CITY_LAT", "19.2183"))
        self.default_lon = float(os.getenv("CITY_LON", "73.0867"))
        self.keys = {
            "data_gov_india": os.getenv("DATA_GOV_INDIA_API_KEY", ""),
            "tomorrowio": os.getenv("TOMORROW_IO_API_KEY", ""),
            "predicthq": os.getenv("PREDICT_HQ_API_KEY", ""),
            "serpapi": os.getenv("SERPER_API_KEY", ""),
        }

    def get_mandi_prices(self, commodity: str = "Onion") -> Dict[str, Any]:
        url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
        params = {
            "api-key": self.keys["data_gov_india"],
            "format": "json",
            "filters[state]": "Maharashtra",
            "filters[commodity]": commodity,
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            records = response.json().get("records", [])[:5]
            return sanitize_for_bedrock({"mandi_records": records})
        except Exception as exc:
            return {"error": str(exc), "source": "get_mandi_prices"}

    def get_weather_pulse(self) -> Dict[str, Any]:
        url = (
            "https://api.tomorrow.io/v4/weather/realtime"
            f"?location={self.default_lat},{self.default_lon}&apikey={self.keys['tomorrowio']}"
        )
        try:
            response = requests.get(url, headers={"accept": "application/json"}, timeout=10)
            response.raise_for_status()
            payload = response.json().get("data", {}).get("values", {})
            return sanitize_for_bedrock({"weather_metrics": payload})
        except Exception as exc:
            return {"error": str(exc), "source": "get_weather_pulse"}

    def get_local_events(self) -> Dict[str, Any]:
        url = "https://api.predicthq.com/v1/events/"
        headers = {
            "Authorization": f"Bearer {self.keys['predicthq']}",
            "Accept": "application/json",
        }
        params = {
            "location_around.origin": f"{self.default_lat},{self.default_lon}",
            "location_around.scale": "5km",
            "active.gte": self.today.strftime("%Y-%m-%d"),
            "active.lte": (self.today + timedelta(days=15)).strftime("%Y-%m-%d"),
            "rank.gte": 40,
        }
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            return sanitize_for_bedrock({"physical_events": response.json().get("results", [])})
        except Exception as exc:
            return {"error": str(exc), "source": "get_local_events"}

    def get_search_trends(self) -> Dict[str, Any]:
        url = "https://google.serper.dev/search"
        payload = {
            "q": f"trending grocery demand spikes {self.city} March 2026",
            "gl": "in",
            "hl": "en",
            "tbs": "qdr:w",
        }
        headers = {
            "X-API-KEY": self.keys["serpapi"],
            "Content-Type": "application/json",
        }
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
            response.raise_for_status()
            data = response.json()
            return sanitize_for_bedrock(
                {
                    "news": [
                        {"title": r.get("title"), "snippet": r.get("snippet")}
                        for r in data.get("organic", [])[:3]
                    ],
                    "questions": [q.get("question") for q in data.get("peopleAlsoAsk", [])[:2]],
                }
            )
        except Exception as exc:
            return {"error": str(exc), "source": "get_search_trends"}

    def get_upcoming_festivals(self) -> Dict[str, Any]:
        try:
            df = pd.read_csv(os.path.join(self.base_path, "festivals.csv"))
            df["Date"] = pd.to_datetime(df["Date"])
            window = df[(df["Date"] >= self.today) & (df["Date"] <= self.today + timedelta(days=15))]
            return sanitize_for_bedrock({"festivals": window.to_dict(orient="records")})
        except Exception as exc:
            return {"error": str(exc), "source": "get_upcoming_festivals"}

    def get_historical_baseline(self, category: str = "Milk") -> Dict[str, Any]:
        try:
            df = pd.read_csv(os.path.join(self.base_path, "FMCG_2022_2024.csv"))
            df["date"] = pd.to_datetime(df["date"])
            hist_start = self.today.replace(year=2023)
            hist_end = hist_start + timedelta(days=15)
            mask = (df["category"] == category) & (df["date"] >= hist_start) & (df["date"] <= hist_end)
            window = df.loc[mask]
            if window.empty:
                return {"message": f"No historical data for {category} for the selected date window."}
            summary = {
                "historical_category": category,
                "total_units_sold": int(window["units_sold"].sum()),
                "avg_stock_held": round(float(window["stock_available"].mean()), 1),
                "promotion_usage_count": int(window["promotion_flag"].sum()),
                "delivery_speed_days": round(float(window["delivery_days"].mean()), 1),
            }
            return sanitize_for_bedrock({"historical_baseline": summary})
        except Exception as exc:
            return {"error": str(exc), "source": "get_historical_baseline"}


TOOL_CONFIG = [
    {"toolSpec": {"name": "get_mandi_prices", "description": "Wholesale prices.", "inputSchema": {"json": {"type": "object", "properties": {"commodity": {"type": "string"}}, "required": ["commodity"]}}}},
    {"toolSpec": {"name": "get_weather_pulse", "description": "Current weather.", "inputSchema": {"json": {"type": "object", "properties": {}}}}},
    {"toolSpec": {"name": "get_local_events", "description": "15-day local events.", "inputSchema": {"json": {"type": "object", "properties": {}}}}},
    {"toolSpec": {"name": "get_search_trends", "description": "Digital intent.", "inputSchema": {"json": {"type": "object", "properties": {}}}}},
    {"toolSpec": {"name": "get_upcoming_festivals", "description": "15-day cultural dates.", "inputSchema": {"json": {"type": "object", "properties": {}}}}},
    {"toolSpec": {"name": "get_historical_baseline", "description": "Check 2023 sales/inventory for a category.", "inputSchema": {"json": {"type": "object", "properties": {"category": {"type": "string"}}, "required": ["category"]}}}},
    {"toolSpec": {"name": "fetch_memory", "description": "Past insights.", "inputSchema": {"json": {"type": "object", "properties": {}}}}},
]

SYSTEM_PROMPT = (
    "You are the Dombivli Retail Agent. Output ONLY a valid JSON array of objects with keys "
    "category, insight, action, rationale. Use current signals, events, and historical baseline to produce "
    "actionable 15-day recommendations for a kirana retailer."
)


def _tool_router(engine: HyperlocalIntelligence, memory: DynamoMemoryStore, session_id: str) -> Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]]:
    return {
        "get_mandi_prices": lambda input_data: engine.get_mandi_prices(input_data.get("commodity", "Onion")),
        "get_weather_pulse": lambda _: engine.get_weather_pulse(),
        "get_local_events": lambda _: engine.get_local_events(),
        "get_search_trends": lambda _: engine.get_search_trends(),
        "get_upcoming_festivals": lambda _: engine.get_upcoming_festivals(),
        "get_historical_baseline": lambda input_data: engine.get_historical_baseline(input_data.get("category", "Milk")),
        "fetch_memory": lambda _: memory.fetch_recent(session_id),
    }


def run_strategy_agent(
    query: str,
    session_id: str,
    anchor_date: datetime,
    base_path: str,
    region: str = "us-east-1",
) -> Dict[str, Any]:
    engine = HyperlocalIntelligence(base_path=base_path, anchor_date=anchor_date)
    memory = DynamoMemoryStore(region=region)

    bedrock = boto3.client("bedrock-runtime", region_name=region)
    model_id = os.getenv("STRATEGY_MODEL_ID", "amazon.nova-lite-v1:0")

    messages = [{"role": "user", "content": [{"text": query}]}]
    steps: List[Dict[str, Any]] = []
    router = _tool_router(engine, memory, session_id)

    while True:
        response = bedrock.converse(
            modelId=model_id,
            system=[{"text": SYSTEM_PROMPT}],
            messages=messages,
            toolConfig={"tools": TOOL_CONFIG},
        )
        msg = response["output"]["message"]
        messages.append(msg)

        if response.get("stopReason") != "tool_use":
            break

        tool_results: List[Dict[str, Any]] = []
        for block in msg.get("content", []):
            tool_use = block.get("toolUse")
            if not tool_use:
                continue

            name = tool_use["name"]
            tool_input = tool_use.get("input", {})
            tool_use_id = tool_use["toolUseId"]

            steps.append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": f"Executing: {name}",
                    "tool": name,
                }
            )

            tool_func = router.get(name)
            result = tool_func(tool_input) if tool_func else {"error": f"Unknown tool {name}"}

            tool_results.append({"toolResult": {"toolUseId": tool_use_id, "content": [{"json": sanitize_for_bedrock(result)}]}})

        if tool_results:
            messages.append({"role": "user", "content": tool_results})

    report_text = messages[-1].get("content", [{}])[0].get("text", "[]")
    cards = safe_json_extract_array(report_text)
    memory.store(session_id=session_id, tags=["Weekly_Insight"], insight=report_text)

    return {
        "session_id": session_id,
        "query": query,
        "anchor_date": anchor_date.date().isoformat(),
        "steps": steps,
        "cards": cards,
        "raw_report": report_text,
    }