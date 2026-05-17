{{ config(materialized='view') }}

with source as (
    select * from {{ source('raw', 'matches') }}
),

staged as (
    select
        match_id,
        cast(season as integer) as season,
        cast(match_number as integer) as match_number,
        cast(date as date) as match_date,
        venue,
        city,
        team1,
        team2,
        toss_winner,
        toss_decision,
        first_batting,
        second_batting,
        cast(innings1_runs as integer) as innings1_runs,
        cast(innings1_wickets as integer) as innings1_wickets,
        cast(innings1_overs as decimal(4,1)) as innings1_overs,
        cast(innings2_runs as integer) as innings2_runs,
        cast(innings2_wickets as integer) as innings2_wickets,
        cast(innings2_overs as decimal(4,1)) as innings2_overs,
        winner,
        result_type,
        margin,
        player_of_match,
        umpire1,
        umpire2,
        -- derived columns
        innings1_runs + innings2_runs as total_match_runs,
        case when toss_winner = winner then true else false end as toss_winner_won_match,
        case when result_type = 'runs' then true else false end as batting_first_won,
        round(innings1_runs / nullif(innings1_overs, 0), 2) as innings1_run_rate,
        round(innings2_runs / nullif(innings2_overs, 0), 2) as innings2_run_rate,
        current_timestamp as _loaded_at
    from source
)

select * from staged
