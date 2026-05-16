import logging
from sqlalchemy import text
from db import get_engine

logger = logging.getLogger(__name__)

TRANSFORMS = {
    "moving_averages": """
        CREATE OR REPLACE VIEW moving_averages AS
        SELECT
            ticker,
            price_date,
            close,
            ROUND(AVG(close) OVER (
                PARTITION BY ticker
                ORDER BY price_date
                ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
            )::NUMERIC, 4) AS ma_20d,
            ROUND(AVG(close) OVER (
                PARTITION BY ticker
                ORDER BY price_date
                ROWS BETWEEN 49 PRECEDING AND CURRENT ROW
            )::NUMERIC, 4) AS ma_50d
        FROM daily_prices
    """,

    "daily_returns": """
        CREATE OR REPLACE VIEW daily_returns AS
        SELECT
            ticker,
            price_date,
            close,
            LAG(close) OVER (PARTITION BY ticker ORDER BY price_date) AS prev_close,
            ROUND(
                (
                    (close - LAG(close) OVER (PARTITION BY ticker ORDER BY price_date))
                    / NULLIF(LAG(close) OVER (PARTITION BY ticker ORDER BY price_date), 0)
                    * 100
                )::NUMERIC, 4
            ) AS daily_return_pct
        FROM daily_prices
    """,

    "volatility": """
        CREATE OR REPLACE VIEW volatility AS
        SELECT
            ticker,
            price_date,
            close,
            ROUND(STDDEV(close) OVER (
                PARTITION BY ticker
                ORDER BY price_date
                ROWS BETWEEN 19 PRECEDING AND CURRENT ROW
            )::NUMERIC, 4) AS volatility_20d
        FROM daily_prices
    """,

    "ticker_summary": """
        CREATE OR REPLACE VIEW ticker_summary AS
        SELECT
            ticker,
            COUNT(*)                            AS trading_days,
            ROUND(MIN(close)::NUMERIC, 4)       AS min_close,
            ROUND(MAX(close)::NUMERIC, 4)       AS max_close,
            ROUND(AVG(close)::NUMERIC, 4)       AS avg_close,
            ROUND(STDDEV(close)::NUMERIC, 4)    AS std_close,
            MIN(price_date)                     AS from_date,
            MAX(price_date)                     AS to_date
        FROM daily_prices
        GROUP BY ticker
    """
}


def run_transforms(engine):
    with engine.begin() as conn:
        for name, sql in TRANSFORMS.items():
            conn.execute(text(sql))
            logger.info(f"View '{name}' created or updated.")
    logger.info("All transforms complete.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("logs/pipeline.log"),
            logging.StreamHandler()
        ]
    )
    engine = get_engine()
    run_transforms(engine)