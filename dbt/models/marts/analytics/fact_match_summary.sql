{{ config(
    materialized='incremental',
    unique_key='match_id',
    incremental_strategy='merge'
) }}

with matches as (
    select * from {{ ref('stg_matches') }}
    {% if is_incremental() %}
    where _loaded_at > (select max(_loaded_at) from {{ this }})
    {% endif %}
),

ball_agg as (
    select
        match_id,
        sum(case when is_four then 1 else 0 end) as total_fours,
        sum(case when is_six then 1 else 0 end) as total_sixes,
        sum(case when is_dot_ball then 1 else 0 end) as total_dot_balls,
        sum(case when is_wicket then 1 else 0 end) as total_wickets_fell,
        count(*) as total_balls,
        -- Powerplay stats
        sum(case when match_phase = 'powerplay' then runs_scored else 0 end) as powerplay_runs,
        sum(case when match_phase = 'powerplay' and is_wicket then 1 else 0 end) as powerplay_wickets,
        -- Middle overs
        sum(case when match_phase = 'middle' then runs_scored else 0 end) as middle_overs_runs,
        sum(case when match_phase = 'middle' and is_wicket then 1 else 0 end) as middle_overs_wickets,
        -- Death overs
        sum(case when match_phase = 'death' then runs_scored else 0 end) as death_overs_runs,
        sum(case when match_phase = 'death' and is_wicket then 1 else 0 end) as death_overs_wickets
    from {{ ref('stg_ball_events') }}
    group by match_id
)

select
    m.match_id,
    m.season,
    m.match_number,
    m.match_date,
    m.venue,
    m.city,
    m.team1,
    m.team2,
    m.toss_winner,
    m.toss_decision,
    m.first_batting,
    m.second_batting,
    m.innings1_runs,
    m.innings1_wickets,
    m.innings1_overs,
    m.innings1_run_rate,
    m.innings2_runs,
    m.innings2_wickets,
    m.innings2_overs,
    m.innings2_run_rate,
    m.winner,
    m.result_type,
    m.margin,
    m.player_of_match,
    m.total_match_runs,
    m.toss_winner_won_match,
    m.batting_first_won,
    coalesce(b.total_fours, 0) as total_fours,
    coalesce(b.total_sixes, 0) as total_sixes,
    coalesce(b.total_dot_balls, 0) as total_dot_balls,
    coalesce(b.powerplay_runs, 0) as powerplay_runs,
    coalesce(b.powerplay_wickets, 0) as powerplay_wickets,
    coalesce(b.middle_overs_runs, 0) as middle_overs_runs,
    coalesce(b.middle_overs_wickets, 0) as middle_overs_wickets,
    coalesce(b.death_overs_runs, 0) as death_overs_runs,
    coalesce(b.death_overs_wickets, 0) as death_overs_wickets,
    m._loaded_at
from matches m
left join ball_agg b on m.match_id = b.match_id
