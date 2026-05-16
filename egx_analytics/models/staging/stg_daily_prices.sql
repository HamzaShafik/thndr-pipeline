with source as (
    select * from {{ source('raw', 'daily_prices') }}
),

cleaned as (
    select
        ticker,
        price_date,
        open,
        high,
        low,
        close,
        volume,
        ingested_at
    from source
    where close is not null
      and close > 0
      and high >= low
      and price_date <= current_date
)

select * from cleaned