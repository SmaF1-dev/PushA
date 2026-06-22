CREATE TABLE IF NOT EXISTS matchmaking_requests (
    id UUID PRIMARY KEY,
    author_id TEXT NOT NULL,

    min_rank TEXT NOT NULL,
    max_rank TEXT NOT NULL,
    required_player_status TEXT NOT NULL,
    min_teammate_rating DOUBLE PRECISION NOT NULL,
    region TEXT NOT NULL,
    required_roles TEXT[] NOT NULL,
    needed_players INTEGER NOT NULL,
    strategy TEXT NOT NULL,

    status TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS candidates (
    id UUID PRIMARY KEY,
    request_id UUID NOT NULL REFERENCES matchmaking_requests(id) ON DELETE CASCADE,

    player_id TEXT NOT NULL,
    nickname TEXT NOT NULL,
    riot_id TEXT NOT NULL,
    current_rank TEXT NOT NULL,
    region TEXT NOT NULL,
    main_roles TEXT[] NOT NULL,
    status TEXT NOT NULL,
    teammate_rating DOUBLE PRECISION NOT NULL,
    score DOUBLE PRECISION NOT NULL,

    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS match_groups (
    id UUID PRIMARY KEY,
    request_id UUID NOT NULL REFERENCES matchmaking_requests(id) ON DELETE CASCADE,

    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS match_group_members (
    group_id UUID NOT NULL REFERENCES match_groups(id) ON DELETE CASCADE,
    player_id TEXT NOT NULL,

    PRIMARY KEY (group_id, player_id)
);

CREATE INDEX IF NOT EXISTS idx_matchmaking_requests_author_id
ON matchmaking_requests(author_id);

CREATE INDEX IF NOT EXISTS idx_matchmaking_requests_status
ON matchmaking_requests(status);

CREATE INDEX IF NOT EXISTS idx_candidates_request_id
ON candidates(request_id);

CREATE INDEX IF NOT EXISTS idx_match_groups_request_id
ON match_groups(request_id);