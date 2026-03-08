## Requirements Specification: Meridian Commerce Engine

## 1. Project Overview
The Meridian Commerce Engine shall be a decision-support platform for Indian Kirana retailers. It shall combine real-time hyperlocal signals (weather, mandi pricing, local events, search intent) with historical FMCG inventory/sales data to generate actionable stocking, pricing, and replenishment recommendations.

---

## 2. Target Architecture (Cloud-Native, Serverless)

The solution shall follow a serverless AWS architecture with clear separation of frontend delivery, API orchestration, compute, AI, and persistence.

### 2.1 Frontend
- The frontend shall be implemented as an Angular SPA (standalone component architecture, TypeScript).
- The UI shall follow a professional dark-theme design and include responsive layouts for desktop and mobile.
- Static frontend assets shall be hosted in Amazon S3.
- Global delivery and HTTPS shall be provided via Amazon CloudFront in front of S3.

### 2.2 API Layer
- Amazon API Gateway (HTTP API) shall expose backend routes.
- At minimum, the following endpoints shall exist:
  - `POST /strategy`
  - `POST /forecast`
  - `POST /chat`
- CORS shall be enabled for both local development origin(s) and deployed frontend domain.

### 2.3 Compute
- Backend logic shall run on AWS Lambda (Python runtime).
- Each screen shall have a dedicated Lambda handler:
  - Screen 1 -> Strategy Lambda
  - Screen 2 -> Forecast Lambda
  - Screen 3 -> Chat Lambda
- Lambda timeout and memory shall be sized for data + Bedrock workloads (minimum 60 seconds and 1024 MB recommended).

### 2.4 AI/LLM Layer
- Screen 1 shall use Amazon Bedrock Runtime with model `amazon.nova-lite-v1:0` via `converse` API and tool-use loop.
- Screen 3 shall use Amazon Bedrock Knowledge Bases via `retrieve_and_generate` with amazon.nova-2-lite-v1 model ARN configured for the account/region.
- Prompting shall enforce concise, query-specific outputs suitable for retail operators.

### 2.5 Persistence and Data
- Amazon DynamoDB shall be used for agent memory/session insight persistence (replacing local SQLite memory).
- Amazon S3 shall store:
  - frontend static assets,
  - knowledge-base source data,
  - deployment artifacts (as needed).
- Static datasets used by backend logic:
  - `FMCG_2022_2024.csv`
  - `festivals.csv`

### 2.6 Observability
- CloudWatch Logs shall be enabled for all Lambda functions.
- Runtime errors shall be returned with actionable error payloads while preserving API contract.

---

## 3. Functional Requirements

### Screen 1: Hyperlocal Strategy Home
- The system shall provide a **Live Reasoning Feed** showing step-level execution traces from strategy tools.
- Strategy Lambda output shall include ordered execution steps (e.g., `Executing: <tool_name>`) so UI can replay with timed progression.
- The system shall return **Insight Cards** with:
  - `category`
  - `insight`
  - `action`
  - `rationale`
- The screen shall include a user-triggered action button (**Generate Insights**) and shall not auto-trigger API execution on page load.
- Strategy calculations shall default to current date unless explicitly overridden by request payload.

### Screen 2: Predictive Forecasts
- The system shall produce 15-day demand projections using a time-series forecasting approach (TFT-class or equivalent production baseline).
- The forecast engine shall compare projected demand against 2023 historical baseline window.
- The system shall calculate stock-to-sales risk and identify SKUs/categories with projected shortfall.
- The implementation shall support schema variance (`sku_id` vs `sku`) in source data without failure.

### Screen 3: Virtual Category Manager (Chat)
- The system shall provide conversational RAG over FMCG data through Bedrock Knowledge Bases.
- The chat assistant shall incorporate Kirana domain semantics including:
  - `pack_type` (Single vs Carton)
  - `promotion_flag`
- Responses shall be concise, directly answer user intent, and preserve actionable retail guidance.
- UI shall support suggested prompt interactions and readable formatted assistant responses.

---

## 4. Data and Integration Requirements

### 4.1 Mandatory Data Assets
- `FMCG_2022_2024.csv` shall be used for:
  - forecasting (Screen 2),
  - retrieval context (Screen 3),
  - historical baseline in strategy reasoning (Screen 1).
- `festivals.csv` shall be used in Screen 1 strategy generation.

### 4.2 External Hyperlocal APIs (Screen 1 tools)
The backend shall support integration with:
- Data.gov.in mandi price API
- Tomorrow.io weather API
- PredictHQ events API
- Serper search API

### 4.3 Session and Memory
- DynamoDB table shall store session-scoped strategy memory with timestamp ordering.
- Recent insight retrieval shall be available as an internal tool for iterative agent reasoning.

---

## 5. API and Contract Requirements

- All three screens shall call backend via Lambda-backed API routes only.
- Response contracts shall include structured JSON payloads suitable for UI rendering.
- Handlers shall provide robust error handling and return machine-readable error objects on failure.
- Date fields shall use `YYYY-MM-DD` format.

---

## 6. Tech Stack Requirements (Implemented Stack as Requirement Baseline)

### Frontend
- Angular (standalone components)
- TypeScript
- RxJS + Angular HttpClient
- CSS (custom theme system)

### Backend
- Python
- `boto3` / `botocore`
- `pandas`
- `requests`

### AWS
- Amazon S3
- Amazon CloudFront
- Amazon API Gateway (HTTP API)
- AWS Lambda
- Amazon Bedrock Runtime
- Amazon Bedrock Knowledge Bases / Agent Runtime
- Amazon DynamoDB
- Amazon CloudWatch Logs

### Packaging/Delivery
- Serverless packaging compatible with Lambda Linux runtime
- Infrastructure template managed through AWS SAM-compatible definitions

---

## 7. Non-Functional Requirements
- Production-grade CORS and HTTPS support.
- Deterministic, parseable output for strategy cards and forecast objects.
- Graceful fallback behavior for missing optional external signals.
- UI shall present useful pre-run states (no blank first-load screens).
- Deployment shall support S3 + CloudFront frontend rollout and API endpoint updates without codebase restructuring.

---