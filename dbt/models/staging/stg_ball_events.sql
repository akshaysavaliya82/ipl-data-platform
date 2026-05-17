{{ config(materialized='view') }}

with source as (
    select * from {{ source('raw', 'ball_events') }}
),

staged as (
    select
        ball_id,
        match_id,
        cast(season as integer) as season,
        cast(innings as integer) as innings,
        cast("over" as integer) as over_number,
        cast(ball as integer) as ball_number_in_over,
        batting_team,
        bowling_team,
        batsman,
        non_striker,
        bowler,
        cast(runs_scored as integer) as runs_scored,
        cast(extras as integer) as extras,
        extras_type,
        cast(is_wicket as boolean) as is_wicket,
        dismissal_type,
        -- derived columns
        ("over" * 6 + ball + 1) as ball_number,
        case when runs_scored = 0 and extras = 0 then true else false end as is_dot_ball,
        case when runs_scored in (4, 6) then true else false end as is_boundary,
        case when runs_scored = 4 then true else false end as is_four,
        case when runs_scored = 6 then true else false end as is_six,
        case
            when "over" < 6 then 'powerplay'
            when "over" < 16 then 'middle'
            else 'death'
        end as match_phase,
        current_timestamp as _loaded_at
    from source
)

select * from staged
