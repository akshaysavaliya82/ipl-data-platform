{{ config(materialized='table') }}

with matches as (
    select * from {{ ref('stg_matches') }}
),

team_as_team1 as (
    select
        team1 as team_name,
        count(*) as matches_played,
        sum(case when winner = team1 then 1 else 0 end) as wins
    from matches
    group by team1
),

team_as_team2 as (
    select
        team2 as team_name,
        count(*) as matches_played,
        sum(case when winner = team2 then 1 else 0 end) as wins
    from matches
    group by team2
),

combined as (
    select
        team_name,
        sum(matches_played) as total_matches,
        sum(wins) as total_wins
    from (
        select * from team_as_team1
        union all
        select * from team_as_team2
    ) t
    group by team_name
),

team_seasons as (
    select
        team_name,
        min(season) as first_season,
        max(season) as last_season,
        count(distinct season) as seasons_played
    from (
        select team1 as team_name, season from matches
        union
        select team2 as team_name, season from matches
    ) ts
    group by team_name
)

select
    row_number() over (order by c.team_name) as team_id,
    c.team_name,
    c.total_matches,
    c.total_wins,
    c.total_matches - c.total_wins as total_losses,
    round(c.total_wins::numeric / nullif(c.total_matches, 0) * 100, 2) as win_percentage,
    ts.first_season,
    ts.last_season,
    ts.seasons_played,
    current_timestamp as _updated_at
from combined c
join team_seasons ts on c.team_name = ts.team_name
order by win_percentage desc
