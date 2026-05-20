# EGX Market Data Pipeline

A data engineering pipeline that ingests daily OHLCV (Open, High, Low, Close, Volume) data for Egyptian Exchange (EGX) stocks, runs automated data quality checks, and produces analytical models using dbt.

## Architecture

```
Yahoo Finance API
       │
       ▼
 Python Ingest
 (yfinance + SQLAlchemy)
       │
       ▼
PostgreSQL Database
 ┌─────────────────┐
 │ stocks          │
 │ daily_prices    │
 │ data_quality_log│
 └─────────────────┘
       │
       ▼
 Quality Checks
 (6 automated checks)
       │
       ▼
 dbt Models
 ┌─────────────────────┐
 │ staging/            │
 │   stg_daily_prices  │
 │   stg_stocks        │
 │ marts/              │
 │   mart_stock_analytics│
 │   mart_ticker_summary │
 └─────────────────────┘
```

## Schema Design

### `stocks`
Stores metadata for each tracked ticker. Primary key on `ticker`.

### `daily_prices`
Stores daily OHLCV data. Composite primary key on `(ticker, price_date)` enforces uniqueness and prevents duplicate ingestion. `close` is stored as `NUMERIC(12,4)` — not `FLOAT` — to avoid floating point rounding errors, which matter in financial data.

An index on `(ticker, price_date DESC)` accelerates time-series queries that filter by ticker and order by date.

### `data_quality_log`
Audit table that logs any data quality violations caught during pipeline runs.

## Design Decisions

**Idempotent ingestion:** All inserts use `ON CONFLICT DO NOTHING`. Running the pipeline multiple times produces the same result — no duplicates, no errors. This is essential for safe retries and backfills.

**NUMERIC over FLOAT for prices:** Floating point types cannot represent all decimal values exactly. In financial contexts, `0.1 + 0.2 != 0.3` in IEEE 754. PostgreSQL's `NUMERIC` type is exact and safe for monetary values.

**Quality checks before transforms:** The pipeline runs data quality checks before dbt models are refreshed. Downstream consumers should never see unvalidated data.

**dbt for the analytical layer:** Models are organised into staging (clean and validate raw data) and marts (business-level analytics). This separation makes the lineage clear and each layer independently testable.

## dbt Models

### Staging
| Model | Description |
|---|---|
| `stg_daily_prices` | Cleans raw price data — filters nulls, negative prices, and future dates |
| `stg_stocks` | Passes through stock metadata from the raw source |

### Marts
| Model | Description |
|---|---|
| `mart_stock_analytics` | Per-ticker daily analytics: 20/50-day moving averages, daily return %, 20-day rolling volatility |
| `mart_ticker_summary` | Aggregate stats per ticker: min, max, avg, std close, trading day count |

## dbt Tests

| Test | Column |
|---|---|
| `not_null` | `daily_prices.ticker`, `daily_prices.price_date`, `daily_prices.close`, `stocks.ticker` |
| `unique` | `stocks.ticker` |

## Data Quality Checks

| Check | Description |
|---|---|
| `null_close` | Close price must not be NULL |
| `negative_price` | Open, high, low, close must all be non-negative |
| `negative_volume` | Volume must be non-negative |
| `high_lower_than_low` | High must be >= low |
| `future_date` | Price date must not be in the future |
| `close_outside_high_low` | Close must be within high/low range |

## Stack

- **Python** — ingestion, orchestration, quality checks
- **PostgreSQL** — storage
- **dbt Core** — data transformation and testing
- **SQLAlchemy** — database connection and query execution
- **yfinance** — Yahoo Finance API wrapper
- **Git** — version control

## How to Run

1. Clone the repository
2. Install dependencies:
```bash
   pip install yfinance sqlalchemy psycopg2-binary pandas python-dotenv dbt-postgres
```
3. Create a `.env` file in the root:
```
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=thndr_pipeline
   DB_USER=postgres
   DB_PASSWORD=your_password
```
4. Create the database and schema using the SQL in `schema.sql`
5. Run the full pipeline:
```bash
   python src/pipeline.py
```
6. Run dbt models:
```bash
   cd egx_analytics
   dbt run
   dbt test
```

## What I'd Add in Production

- **Airflow DAGs** to schedule, monitor, and retry the pipeline automatically
- **Incremental dbt models** — currently rebuilds all views on every run; production would process only new trading days
- **Alerting** on quality check failures via email or Slack
- **Cloud deployment** — GCS for raw storage, BigQuery as the warehouse, Cloud Composer for orchestration

## Tickers Tracked

| Ticker | Company |
|---|---|
| COMI.CA | Commercial International Bank |
| ETEL.CA | Telecom Egypt |
| SWDY.CA | El Sewedy Electric |
| EFIH.CA | EFG Hermes |
| HRHO.CA | Hermes Holding |
