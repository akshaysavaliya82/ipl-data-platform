-- Initialize PostgreSQL databases for IPL Analytics Platform

-- Create main analytics database tables
CREATE TABLE IF NOT EXISTS matches (
    match_id VARCHAR(50) PRIMARY KEY,
    season INTEGER NOT NULL,
    match_number INTEGER,
    date DATE,
    venue VARCHAR(200),
    city VARCHAR(100),
    team1 VARCHAR(100) NOT NULL,
    team2 VARCHAR(100) NOT NULL,
    toss_winner VARCHAR(100),
    toss_decision VARCHAR(20),
    first_batting VARCHAR(100),
    second_batting VARCHAR(100),
    innings1_runs INTEGER DEFAULT 0,
    innings1_wickets INTEGER DEFAULT 0,
    innings1_overs DECIMAL(4,1),
    innings2_runs INTEGER DEFAULT 0,
    innings2_wickets INTEGER DEFAULT 0,
    innings2_overs DECIMAL(4,1),
    winner VARCHAR(100),
    result_type VARCHAR(50),
    margin VARCHAR(50),
    player_of_match VARCHAR(100),
    umpire1 VARCHAR(100),
    umpire2 VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ball_events (
    ball_id VARCHAR(100) PRIMARY KEY,
    match_id VARCHAR(50) REFERENCES matches(match_id),
    season INTEGER,
    innings INTEGER NOT NULL,
    "over" INTEGER NOT NULL,
    ball INTEGER NOT NULL,
    batting_team VARCHAR(100),
    bowling_team VARCHAR(100),
    batsman VARCHAR(100) NOT NULL,
    non_striker VARCHAR(100),
    bowler VARCHAR(100) NOT NULL,
    runs_scored INTEGER DEFAULT 0,
    extras INTEGER DEFAULT 0,
    extras_type VARCHAR(50),
    is_wicket BOOLEAN DEFAULT FALSE,
    dismissal_type VARCHAR(50),
    is_four BOOLEAN DEFAULT FALSE,
    is_six BOOLEAN DEFAULT FALSE,
    is_boundary BOOLEAN DEFAULT FALSE,
    is_dot_ball BOOLEAN DEFAULT FALSE,
    phase VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS players (
    player_id VARCHAR(50) PRIMARY KEY,
    player_name VARCHAR(100) NOT NULL,
    nationality VARCHAR(50),
    date_of_birth DATE,
    batting_style VARCHAR(50),
    bowling_style VARCHAR(100),
    role VARCHAR(50),
    ipl_debut_year INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS teams (
    team_id SERIAL PRIMARY KEY,
    team_name VARCHAR(100) NOT NULL UNIQUE,
    short_name VARCHAR(10),
    home_city VARCHAR(100),
    home_venue VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS venues (
    venue_id SERIAL PRIMARY KEY,
    venue_name VARCHAR(200) NOT NULL,
    city VARCHAR(100),
    country VARCHAR(50) DEFAULT 'India',
    capacity INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_matches_season ON matches(season);
CREATE INDEX IF NOT EXISTS idx_matches_winner ON matches(winner);
CREATE INDEX IF NOT EXISTS idx_matches_venue ON matches(venue);
CREATE INDEX IF NOT EXISTS idx_ball_events_match ON ball_events(match_id);
CREATE INDEX IF NOT EXISTS idx_ball_events_batsman ON ball_events(batsman);
CREATE INDEX IF NOT EXISTS idx_ball_events_bowler ON ball_events(bowler);
CREATE INDEX IF NOT EXISTS idx_ball_events_season ON ball_events(season);

-- Create Airflow database
CREATE DATABASE airflow;
GRANT ALL PRIVILEGES ON DATABASE airflow TO ipl_admin;
