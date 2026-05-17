{{ config(materialized='table') }}

with matches as (
    select * from {{ ref('stg_matches') }}
),

venue_stats as (
    select
        venue,
        city,
        count(*) as matches_hosted,
        round(avg(total_match_runs)::numeric, 1) as avg_match_total,
        round(avg(innings1_runs)::numeric, 1) as avg_first_innings_score,
        round(avg(innings2_runs)::numeric, 1) as avg_second_innings_score,
        sum(case when batting_first_won then 1 else 0 end) as bat_first_wins,
        sum(case when not batting_first_won then 1 else 0 end) as chase_wins,
        round(
            sum(case when batting_first_won then 1 else 0 end)::numeric /
            nullif(count(*), 0) * 100, 2
        ) as bat_first_win_pct,
        round(avg(innings1_run_rate)::numeric, 2) as avg_first_innings_rr,
        round(avg(innings2_run_rate)::numeric, 2) as avg_second_innings_rr,
        min(season) as first_match_season,
        max(season) as last_match_season
    from matches
    group by venue, city
)

select
    row_number() over (order by venue) as venue_id,
    venue as venue_name,
    city,
    'India' as country,
    matches_hosted,
    avg_match_total,
    avg_first_innings_score,
    avg_second_innings_score,
    bat_first_wins,
    chase_wins,
    bat_first_win_pct,
    100 - bat_first_win_pct as chase_win_pct,
    avg_first_innings_rr,
    avg_second_innings_rr,
    first_match_season,
    last_match_season,
    current_timestamp as _updated_at
from venue_stats
