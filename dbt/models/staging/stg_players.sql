{{ config(materialized='view') }}

with source as (
    select * from {{ source('raw', 'players') }}
),

staged as (
    select
        player_id,
        player_name,
        nationality,
        cast(date_of_birth as date) as date_of_birth,
        batting_style,
        bowling_style,
        role as player_role,
        cast(ipl_debut_year as integer) as ipl_debut_year,
        current_timestamp as _loaded_at
    from source
)

select * from staged
