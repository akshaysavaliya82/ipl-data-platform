{{ config(materialized='ephemeral') }}

with ball_events as (
    select * from {{ ref('stg_ball_events') }}
),

batting_stats as (
    select
        season,
        match_id,
        batsman as player_name,
        batting_team as team,
        innings,
        sum(runs_scored) as runs,
        count(*) as balls_faced,
        sum(case when is_four then 1 else 0 end) as fours,
        sum(case when is_six then 1 else 0 end) as sixes,
        sum(case when is_dot_ball then 1 else 0 end) as dot_balls,
        sum(case when is_boundary then 1 else 0 end) as boundaries,
        max(case when is_wicket then 1 else 0 end) as was_dismissed,
        round(sum(runs_scored)::numeric / nullif(count(*), 0) * 100, 2) as strike_rate
    from ball_events
    group by season, match_id, batsman, batting_team, innings
)

select * from batting_stats
