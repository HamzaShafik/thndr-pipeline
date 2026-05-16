with prices as (
    select * from {{ ref('stg_daily_prices') }}
),

stocks as (
    select * from {{ ref('stg_stocks') }}
),

analytics as (
    select
        p.ticker,
        s.name,
        s.market,
        p.price_date,
        p.open,
        p.high,
        p.low,
        p.close,
        p.volume,

        -- moving averages
        round(avg(p.close) over (
            partition by p.ticker
            order by p.price_date
            rows between 19 preceding and current row
        )::numeric, 4) as ma_20d,

        round(avg(p.close) over (
            partition by p.ticker
            order by p.price_date
            rows between 49 preceding and current row
        )::numeric, 4) as ma_50d,

        -- daily return
        round((
            (p.close - lag(p.close) over (partition by p.ticker order by p.price_date))
            / nullif(lag(p.close) over (partition by p.ticker order by p.price_date), 0)
            * 100
        )::numeric, 4) as daily_return_pct,

        -- rolling volatility
        round(stddev(p.close) over (
            partition by p.ticker
            order by p.price_date
            rows between 19 preceding and current row
        )::numeric, 4) as volatility_20d

    from prices p
    left join stocks s on p.ticker = s.ticker
)

select * from analytics