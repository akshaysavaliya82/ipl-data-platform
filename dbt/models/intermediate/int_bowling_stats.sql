{{ config(materialized='ephemeral') }}

with ball_events as (
    select * from {{ ref('stg_ball_events') }}
),

bowling_stats as (
    select
        season,
        match_id,
        bowler as player_name,
        bowling_team as team,
        innings,
        sum(runs_scored) as runs_conceded,
        count(*) as balls_bowled,
        sum(case when is_wicket then 1 else 0 end) as wickets,
        sum(case when is_dot_ball then 1 else 0 end) as dot_balls,
        round(count(*)::numeric / 6, 1) as overs_bowled,
        round(
            sum(runs_scored)::numeric / nullif(round(count(*)::numeric / 6, 1), 0),
            2
        ) as economy_rate
    from ball_events
    group by season, match_id, bowler, bowling_team, innings
)

select * from bowling_stats
