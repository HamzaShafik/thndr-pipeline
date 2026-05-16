with source as (
    select * from {{ source('raw', 'stocks') }}
)

select
    ticker,
    name,
    market,
    created_at
from source