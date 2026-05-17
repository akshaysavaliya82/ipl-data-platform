{{ config(materialized='table') }}

with players as (
    select * from {{ ref('stg_players') }}
),

career_batting as (
    select
        player_name,
        count(distinct match_id) as matches_played,
        sum(runs) as total_runs,
        sum(balls_faced) as total_balls_faced,
        sum(fours) as total_fours,
        sum(sixes) as total_sixes,
        max(runs) as highest_score,
        round(avg(runs)::numeric, 2) as batting_average,
        round(sum(runs)::numeric / nullif(sum(balls_faced), 0) * 100, 2) as career_strike_rate,
        sum(case when runs >= 50 then 1 else 0 end) as fifties,
        sum(case when runs >= 100 then 1 else 0 end) as centuries
    from {{ ref('int_batting_stats') }}
    group by player_name
),

career_bowling as (
    select
        player_name,
        sum(wickets) as total_wickets,
        sum(runs_conceded) as total_runs_conceded,
        sum(balls_bowled) as total_balls_bowled,
        round(avg(economy_rate)::numeric, 2) as career_economy,
        max(wickets) as best_bowling_wickets
    from {{ ref('int_bowling_stats') }}
    group by player_name
)

select
    p.player_id,
    p.player_name,
    p.nationality,
    p.date_of_birth,
    p.batting_style,
    p.bowling_style,
    p.player_role,
    p.ipl_debut_year,
    coalesce(cb.matches_played, 0) as matches_played,
    coalesce(cb.total_runs, 0) as total_runs,
    coalesce(cb.total_balls_faced, 0) as total_balls_faced,
    coalesce(cb.total_fours, 0) as total_fours,
    coalesce(cb.total_sixes, 0) as total_sixes,
    coalesce(cb.highest_score, 0) as highest_score,
    coalesce(cb.batting_average, 0) as batting_average,
    coalesce(cb.career_strike_rate, 0) as career_strike_rate,
    coalesce(cb.fifties, 0) as fifties,
    coalesce(cb.centuries, 0) as centuries,
    coalesce(cbo.total_wickets, 0) as total_wickets,
    coalesce(cbo.career_economy, 0) as career_economy,
    coalesce(cbo.best_bowling_wickets, 0) as best_bowling_figures,
    current_timestamp as _updated_at
from players p
left join career_batting cb on p.player_name = cb.player_name
left join career_bowling cbo on p.player_name = cbo.player_name
