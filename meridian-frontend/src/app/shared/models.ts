export interface StrategyCard {
  category: string;
  insight: string;
  action: string;
  rationale: string;
}

export interface StrategyStep {
  timestamp: string;
  message: string;
  tool: string;
}

export interface StrategyResponse {
  session_id: string;
  query: string;
  anchor_date: string;
  steps: StrategyStep[];
  cards: StrategyCard[];
  raw_report: string;
}

export interface ForecastPoint {
  date: string;
  category: string;
  predicted_units_sold: number;
}

export interface ForecastRisk {
  sku_id: string;
  category: string;
  projected_demand_15d: number;
  stock_available: number;
  stock_to_sales_ratio: number;
  risk_level: string;
  baseline_2023_units: number;
}

export interface ForecastResponse {
  anchor_date: string;
  model: string;
  forecast_by_day_category: ForecastPoint[];
  stockout_risks: ForecastRisk[];
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatResponse {
  session_id: string;
  answer: string;
  citations: unknown[];
  error?: string;
}