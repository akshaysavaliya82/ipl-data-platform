{% snapshot scd_team_stats %}

{{
    config(
      target_schema='snapshots',
      unique_key='team_name',
      strategy='check',
      check_cols=['total_matches', 'total_wins', 'win_percentage'],
    )
}}

select * from {{ ref('dim_team') }}

{% endsnapshot %}
