{{ config(
    materialized='incremental',
    unique_key=['match_id', 'player_name'],
    incremental_strategy='merge'
) }}

with batting as (
    select
        season,
        match_id,
        player_name,
        team,
        innings,
        runs,
        balls_faced,
        fours,
        sixes,
        dot_balls,
        boundaries,
        was_dismissed,
        strike_rate
    from {{ ref('int_batting_stats') }}
),

bowling as (
    select
        season,
        match_id,
        player_name,
        team,
        innings,
        runs_conceded,
        balls_bowled,
        wickets,
        dot_balls as bowling_dot_balls,
        overs_bowled,
        economy_rate
    from {{ ref('int_bowling_stats') }}
),

combined as (
    select
        coalesce(bat.season, bowl.season) as season,
        coalesce(bat.match_id, bowl.match_id) as match_id,
        coalesce(bat.player_name, bowl.player_name) as player_name,
        coalesce(bat.team, bowl.team) as team,
        -- Batting stats
        coalesce(bat.runs, 0) as batting_runs,
        coalesce(bat.balls_faced, 0) as balls_faced,
        coalesce(bat.fours, 0) as fours,
        coalesce(bat.sixes, 0) as sixes,
        coalesce(bat.strike_rate, 0) as strike_rate,
        coalesce(bat.was_dismissed, 0) as was_dismissed,
        -- Bowling stats
        coalesce(bowl.wickets, 0) as wickets,
        coalesce(bowl.runs_conceded, 0) as runs_conceded,
        coalesce(bowl.overs_bowled, 0) as overs_bowled,
        coalesce(bowl.economy_rate, 0) as economy_rate,
        coalesce(bowl.bowling_dot_balls, 0) as bowling_dot_balls,
        -- Fantasy points (simplified)
        (
            coalesce(bat.runs, 0) * 1.0 +
            coalesce(bat.fours, 0) * 1.0 +
            coalesce(bat.sixes, 0) * 2.0 +
            coalesce(bowl.wickets, 0) * 25.0 +
            case when coalesce(bat.runs, 0) >= 50 then 25 else 0 end +
            case when coalesce(bat.runs, 0) >= 100 then 50 else 0 end +
            case when coalesce(bowl.wickets, 0) >= 3 then 25 else 0 end
        ) as fantasy_points,
        current_timestamp as _loaded_at
    from batting bat
    full outer join bowling bowl
        on bat.match_id = bowl.match_id
        and bat.player_name = bowl.player_name
)

select * from combined
{% if is_incremental() %}
where _loaded_at > (select max(_loaded_at) from {{ this }})
{% endif %}
