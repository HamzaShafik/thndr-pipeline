import logging
from sqlalchemy import text
from db import get_engine

logger = logging.getLogger(__name__)


def run_quality_checks(engine):
    checks = [
        (
            "null_close",
            """
            SELECT ticker, price_date, 'null_close' AS check_name, 'Close price is NULL' AS issue
            FROM daily_prices
            WHERE close IS NULL
            """
        ),
        (
            "negative_price",
            """
            SELECT ticker, price_date, 'negative_price' AS check_name, 'One or more prices are negative' AS issue
            FROM daily_prices
            WHERE open < 0 OR high < 0 OR low < 0 OR close < 0
            """
        ),
        (
            "negative_volume",
            """
            SELECT ticker, price_date, 'negative_volume' AS check_name, 'Volume is negative' AS issue
            FROM daily_prices
            WHERE volume < 0
            """
        ),
        (
            "high_lower_than_low",
            """
            SELECT ticker, price_date, 'high_lower_than_low' AS check_name, 'High is lower than low' AS issue
            FROM daily_prices
            WHERE high < low
            """
        ),
        (
            "future_date",
            """
            SELECT ticker, price_date, 'future_date' AS check_name, 'Price date is in the future' AS issue
            FROM daily_prices
            WHERE price_date > CURRENT_DATE
            """
        ),
        (
            "close_outside_high_low",
            """
            SELECT ticker, price_date, 'close_outside_high_low' AS check_name, 'Close is outside high/low range' AS issue
            FROM daily_prices
            WHERE close > high OR close < low
            """
        )
    ]

    total_issues = 0

    with engine.begin() as conn:
        for check_name, query in checks:
            rows = conn.execute(text(query)).fetchall()

            if rows:
                for row in rows:
                    conn.execute(text("""
                        INSERT INTO data_quality_log (ticker, price_date, check_name, issue)
                        VALUES (:ticker, :price_date, :check_name, :issue)
                    """), {
                        "ticker": row.ticker,
                        "price_date": row.price_date,
                        "check_name": row.check_name,
                        "issue": row.issue
                    })
                logger.warning(f"[{check_name}] {len(rows)} issue(s) found.")
                total_issues += len(rows)
            else:
                logger.info(f"[{check_name}] passed.")

    if total_issues == 0:
        logger.info("All quality checks passed. Data is clean.")
    else:
        logger.warning(f"Quality checks complete. {total_issues} total issue(s) logged.")


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
    run_quality_checks(engine)