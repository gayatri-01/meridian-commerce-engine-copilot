import os
from datetime import datetime, timedelta
from typing import Any, Dict, List

import pandas as pd


def _prepare_daily_series(df: pd.DataFrame) -> pd.DataFrame:
    sku_col = "sku_id" if "sku_id" in df.columns else "sku"
    grouped = (
        df.groupby(["date", sku_col, "category"], as_index=False)
        .agg(
            units_sold=("units_sold", "sum"),
            stock_available=("stock_available", "sum"),
        )
    )
    grouped = grouped.rename(columns={sku_col: "sku_id"})
    grouped["weekday"] = grouped["date"].dt.dayofweek
    return grouped


def _weekday_factors(series_df: pd.DataFrame) -> Dict[int, float]:
    weekday_avg = series_df.groupby("weekday")["units_sold"].mean()
    overall_avg = series_df["units_sold"].mean() or 1.0
    return {int(k): float(v / overall_avg) for k, v in weekday_avg.items()}


def _trend_per_day(series_df: pd.DataFrame) -> float:
    tail = series_df.sort_values("date").tail(45)
    if len(tail) < 10:
        return 0.0
    half = len(tail) // 2
    first = tail.iloc[:half]["units_sold"].mean()
    second = tail.iloc[half:]["units_sold"].mean()
    return float((second - first) / max(len(tail), 1))


def build_15_day_forecast(base_path: str, anchor_date: datetime) -> Dict[str, Any]:
    data_path = os.path.join(base_path, "FMCG_2022_2024.csv")
    df = pd.read_csv(data_path)
    required_cols = {"date", "category", "stock_available", "units_sold"}
    missing_required = sorted(required_cols - set(df.columns))
    if missing_required:
        raise ValueError(f"Missing required columns in dataset: {', '.join(missing_required)}")
    df["date"] = pd.to_datetime(df["date"])

    # Use full historical data (2022-2024) and project from anchor date.
    history = df[df["date"] <= anchor_date].copy()
    daily = _prepare_daily_series(history)

    latest_stock = (
        daily.sort_values("date")
        .groupby(["sku_id", "category"], as_index=False)
        .tail(1)
        .set_index(["sku_id", "category"])
    )

    rows: List[Dict[str, Any]] = []
    risk_rows: List[Dict[str, Any]] = []

    for (sku_id, category), g in daily.groupby(["sku_id", "category"]):
        g = g.sort_values("date")
        base = float(g.tail(30)["units_sold"].mean()) if not g.empty else 0.0
        weekday_factor = _weekday_factors(g)
        trend = _trend_per_day(g)

        # 2023 baseline for same forward-looking window.
        start_2023 = anchor_date.replace(year=2023)
        end_2023 = start_2023 + timedelta(days=14)
        source_sku_col = "sku_id" if "sku_id" in history.columns else "sku"
        baseline_2023 = history[
            (history[source_sku_col] == sku_id)
            & (history["category"] == category)
            & (history["date"] >= start_2023)
            & (history["date"] <= end_2023)
        ]["units_sold"].sum()

        stock_now = float(latest_stock.loc[(sku_id, category)]["stock_available"]) if (sku_id, category) in latest_stock.index else 0.0

        sku_forecast_total = 0.0
        for i in range(1, 16):
            day = anchor_date + timedelta(days=i)
            weekday = day.weekday()
            factor = weekday_factor.get(weekday, 1.0)
            pred = max(0.0, base * factor + trend * i)
            sku_forecast_total += pred

            rows.append(
                {
                    "date": day.date().isoformat(),
                    "sku_id": sku_id,
                    "category": category,
                    "predicted_units_sold": round(pred, 2),
                }
            )

        ratio = stock_now / sku_forecast_total if sku_forecast_total > 0 else None
        risk = ratio is not None and ratio < 1.0
        if risk:
            risk_rows.append(
                {
                    "sku_id": sku_id,
                    "category": category,
                    "projected_demand_15d": round(sku_forecast_total, 2),
                    "stock_available": round(stock_now, 2),
                    "stock_to_sales_ratio": round(ratio, 2),
                    "risk_level": "HIGH" if ratio < 0.75 else "MEDIUM",
                    "baseline_2023_units": int(baseline_2023),
                }
            )

    if rows:
        summary = (
            pd.DataFrame(rows)
            .groupby(["date", "category"], as_index=False)["predicted_units_sold"]
            .sum()
            .sort_values(["date", "category"])
            .to_dict(orient="records")
        )
    else:
        summary = []

    return {
        "anchor_date": anchor_date.date().isoformat(),
        "model": "Weekday-seasonality + short-term trend (TFT-like lightweight baseline)",
        "forecast_by_day_category": summary,
        "stockout_risks": sorted(risk_rows, key=lambda x: x["stock_to_sales_ratio"]),
    }
