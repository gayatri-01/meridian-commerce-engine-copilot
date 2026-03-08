# Meridian Commerce Engine

AI-powered anticipatory commerce system designed for **Indian Kirana
(neighborhood retail) stores**.

It combines **hyperlocal signals, historical FMCG data, and AI
reasoning** to generate **actionable inventory, pricing, and
replenishment recommendations**.

The platform provides **predictive demand forecasting, explainable
insights, and a conversational category manager** to support smarter
retail decisions.

------------------------------------------------------------------------

# Overview

Traditional kirana retail inventory decisions rely heavily on intuition
and historical patterns.

**Meridian Commerce Engine augments this with:**

-   Hyperlocal intelligence from weather, mandi prices, local events,
    and search trends
-   AI-powered reasoning with explainable recommendations
-   Predictive demand forecasting to reduce stockouts and overstock
-   Conversational FMCG analytics through Retrieval Augmented Generation
    (RAG)

The platform is built as a **serverless, cloud-native system on AWS**.

------------------------------------------------------------------------

# Key Features

## Hyperlocal Strategy Engine

Generates AI-driven insights for stocking and pricing decisions using:

-   Weather forecasts
-   Mandi commodity prices
-   Local events and festivals
-   Search demand signals
-   Historical FMCG sales data

Outputs **Insight Cards** with:

-   category
-   insight
-   action
-   rationale

------------------------------------------------------------------------

## Predictive Demand Forecasting

Forecasts **15-day demand projections** using historical FMCG data.

Capabilities:

-   Time-series demand forecasting
-   Risk detection for stockouts
-   Comparison with historical baselines
-   SKU-level projections

------------------------------------------------------------------------

## Virtual Category Manager (AI Chat)

Conversational assistant for FMCG data insights.

Example questions:

-   Which beverages will sell more during summer?
-   Which SKUs should I stock more during Diwali?
-   What products have highest turnover?

Powered by **Bedrock Knowledge Bases + Retrieval Augmented Generation
(RAG)**.

------------------------------------------------------------------------

# System Architecture

    User
      |
    CloudFront CDN
      |
    S3 (Angular SPA)
      |
    API Gateway
      |
    -----------------------------
    | Strategy Lambda           |
    | Forecast Lambda           |
    | Chat Lambda               |
    -----------------------------
         |        |        |
     Bedrock   Pandas   Bedrock KB
         |
    External APIs (Weather, Mandi, Events, Search)

    Persistence
    -----------
    DynamoDB (session memory)
    S3 (datasets + KB data)
    CloudWatch (logs)

------------------------------------------------------------------------

# Tech Stack

## Frontend

-   Angular
-   TypeScript
-   RxJS
-   S3 + CloudFront

## Backend

-   Python
-   AWS Lambda
-   boto3
-   pandas
-   requests

## AI Services

-   Amazon Bedrock
-   Bedrock Knowledge Bases
-   Amazon Nova Lite models

## Storage

-   Amazon S3
-   DynamoDB
-   CloudWatch Logs

## Infrastructure

-   AWS SAM

------------------------------------------------------------------------

# API Endpoints

  Endpoint    Method   Description
  ----------- -------- -------------------------------------
  /strategy   POST     Generate hyperlocal retail insights
  /forecast   POST     Generate 15-day demand forecast
  /chat       POST     Query FMCG knowledge base

------------------------------------------------------------------------

# Data Sources

## Internal

-   FMCG_2022_2024.csv
-   festivals.csv

## External APIs

-   Tomorrow.io Weather API
-   Data.gov.in Mandi Prices
-   PredictHQ Events API
-   Serper Search API

------------------------------------------------------------------------

# Example Insight

``` json
{
  "category": "Beverages",
  "insight": "Temperature spike expected this week",
  "action": "Increase soft drink and packaged water inventory",
  "rationale": "High temperature combined with festival events increases beverage demand"
}
```

------------------------------------------------------------------------

# Deployment

## Install Dependencies

Frontend

    cd frontend
    npm install

Backend

    pip install -r requirements.txt

------------------------------------------------------------------------

## Build

    sam build

## Deploy

    sam deploy --guided

------------------------------------------------------------------------

# Running Locally

Start backend

    sam local start-api

Start frontend

    npm start

------------------------------------------------------------------------

# Observability

-   CloudWatch Logs
-   CloudWatch metrics
-   Structured logging for debugging AI workflows

------------------------------------------------------------------------

# Future Enhancements

-   POS integration
-   Real-time inventory tracking
-   Supplier ordering automation
-   Multi-store support
-   Reinforcement learning demand optimization

------------------------------------------------------------------------