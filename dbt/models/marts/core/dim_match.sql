{{ config(materialized='table') }}

with matches as (
    select * from {{ ref('stg_matches') }}
)

select
    match_id,
    season,
    match_number,
    match_date,
    venue,
    city,
    team1,
    team2,
    toss_winner,
    toss_decision,
    first_batting,
    second_batting,
    winner,
    result_type,
    margin,
    player_of_match,
    umpire1,
    umpire2,
    total_match_runs,
    toss_winner_won_match,
    batting_first_won,
    innings1_run_rate,
    innings2_run_rate,
    case
        when total_match_runs > 400 then 'very_high_scoring'
        when total_match_runs > 350 then 'high_scoring'
        when total_match_runs > 300 then 'moderate'
        when total_match_runs > 250 then 'low_scoring'
        else 'very_low_scoring'
    end as scoring_category,
    current_timestamp as _updated_at
from matches
