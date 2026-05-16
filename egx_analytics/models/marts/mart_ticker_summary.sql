with analytics as (
    select * from {{ ref('mart_stock_analytics') }}
)

select
    ticker,
    name,
    market,
    count(*)                        as trading_days,
    round(min(close)::numeric, 4)  as min_close,
    round(max(close)::numeric, 4)  as max_close,
    round(avg(close)::numeric, 4)  as avg_close,
    round(stddev(close)::numeric, 4) as std_close,
    min(price_date)                as from_date,
    max(price_date)                as to_date
from analytics
group by ticker, name, market