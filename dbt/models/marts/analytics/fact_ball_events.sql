{{ config(
    materialized='incremental',
    unique_key='ball_id',
    incremental_strategy='merge'
) }}

with ball_events as (
    select * from {{ ref('stg_ball_events') }}
    {% if is_incremental() %}
    where _loaded_at > (select max(_loaded_at) from {{ this }})
    {% endif %}
)

select
    ball_id,
    match_id,
    season,
    innings,
    over_number,
    ball_number_in_over,
    ball_number,
    batting_team,
    bowling_team,
    batsman,
    non_striker,
    bowler,
    runs_scored,
    extras,
    extras_type,
    is_wicket,
    dismissal_type,
    is_dot_ball,
    is_boundary,
    is_four,
    is_six,
    match_phase,
    _loaded_at
from ball_events
