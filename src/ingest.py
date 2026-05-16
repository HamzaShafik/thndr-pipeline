import logging
import yfinance as yf
import pandas as pd
from sqlalchemy import text
from db import get_engine

logger = logging.getLogger(__name__)

TICKERS = {
    "EFIH.CA": "EFG Hermes",
    "HRHO.CA": "Hermes Holding",
    "COMI.CA": "Commercial International Bank",
    "ETEL.CA": "Telecom Egypt",
    "SWDY.CA": "El Sewedy Electric"
}


def insert_stocks(engine):
    with engine.begin() as conn:
        for ticker, name in TICKERS.items():
            conn.execute(text("""
                INSERT INTO stocks (ticker, name, market)
                VALUES (:ticker, :name, 'EGX')
                ON CONFLICT (ticker) DO NOTHING
            """), {"ticker": ticker, "name": name})
    logger.info(f"Inserted {len(TICKERS)} stocks into stocks table.")


def fetch_prices(ticker: str, period: str = "6mo") -> pd.DataFrame:
    logger.info(f"Fetching price data for {ticker}...")
    df = yf.download(ticker, period=period, auto_adjust=True, progress=False)

    if df.empty:
        logger.warning(f"No data returned for {ticker}.")
        return pd.DataFrame()

    df = df.reset_index()
    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    df = df.rename(columns={
        "Date": "price_date",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume"
    })
    df["ticker"] = ticker
    df = df[["ticker", "price_date", "open", "high", "low", "close", "volume"]]
    df["price_date"] = pd.to_datetime(df["price_date"]).dt.date
    return df


def insert_prices(engine, df: pd.DataFrame):
    if df.empty:
        return

    inserted = 0
    with engine.begin() as conn:
        for _, row in df.iterrows():
            result = conn.execute(text("""
                INSERT INTO daily_prices (ticker, price_date, open, high, low, close, volume)
                VALUES (:ticker, :price_date, :open, :high, :low, :close, :volume)
                ON CONFLICT (ticker, price_date) DO NOTHING
            """), row.to_dict())
            inserted += result.rowcount

    logger.info(f"Inserted {inserted} new rows for {df['ticker'].iloc[0]}.")


def run_ingestion():
    engine = get_engine()
    insert_stocks(engine)

    for ticker in TICKERS:
        df = fetch_prices(ticker)
        insert_prices(engine, df)

    logger.info("Ingestion complete.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("logs/pipeline.log"),
            logging.StreamHandler()
        ]
    )
    run_ingestion()