# PushA — Valorant Team Finder

PushA is a microservice-based teammate matching system for Valorant. The project allows a player to create a matchmaking request, find suitable teammates, score and filter candidates, and create a match group.

The project is split into two services:

- **Matchmaking Service** — Go service responsible for matchmaking requests, candidate filtering/scoring, group creation, PostgreSQL persistence and REST API.
- **Player Service** — Python service responsible for player profiles, Valorant profiles, teammate reviews and gRPC candidate search.

---

## Architecture

```text
Client / Swagger / Postman
        |
        | REST API
        v
Go Matchmaking Service
        |
        | gRPC
        v
Python Player Service

Go PostgreSQL       Python PostgreSQL
(matchmaking data)  (players, profiles, reviews)
```

### Main flow

```text
1. Create matchmaking request
2. Request candidates from Python Player Service via gRPC
3. Filter candidates using Specification Pattern
4. Score candidates using Strategy Pattern
5. Store candidates in Go PostgreSQL
6. Create a match group from selected candidates
7. Mark matchmaking request as COMPLETED
```

---

## Tech stack

### Go Matchmaking Service

- Go
- net/http + chi router
- PostgreSQL
- pgxpool
- gRPC client
- Swagger / Swaggo
- Unit and handler tests

### Python Player Service

- Python
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- gRPC server
- Pydantic

---

## Repository structure

```text
PushA/
├── services/
│   ├── matchmaking-service/      # Go REST matchmaking service
│   │   ├── cmd/server/           # Application entry point
│   │   ├── internal/api/         # HTTP router, handlers, responses
│   │   ├── internal/apperror/    # Typed application errors
│   │   ├── internal/config/      # Environment configuration
│   │   ├── internal/db/          # PostgreSQL connection pool
│   │   ├── internal/domain/      # Domain models and enums
│   │   ├── internal/dto/         # HTTP request/response DTOs
│   │   ├── internal/provider/    # Mock and gRPC player providers
│   │   ├── internal/repository/  # PostgreSQL repositories
│   │   ├── internal/service/     # Business logic
│   │   ├── migrations/           # Go service DB schema
│   │   ├── pkg/proto/            # Generated Go protobuf code
│   │   └── docs/                 # Generated Swagger docs
│   │
│   └── player-service/           # Python player/profile service
│       ├── app/                  # FastAPI and gRPC application code
│       ├── migrations/           # Alembic migrations
│       ├── scripts/              # Seed data and helper scripts
│       └── tests/                # Python tests
```

---

## Design patterns used

### Strategy Pattern

The Go service uses different scoring strategies for candidates:

- `BALANCED`
- `RANK_FOCUSED`
- `RATING_FOCUSED`
- `ROLE_FOCUSED`

Each strategy calculates candidate score using different weights for rank, teammate rating, role match and status.

### Specification Pattern

Candidate filtering is implemented as a set of independent specifications:

- candidate must not be the request author;
- candidate rank must be within the requested rank range;
- candidate status must match the requested status;
- candidate teammate rating must be high enough;
- candidate region must match;
- candidate role must match at least one required role.

### Provider / Adapter

The matchmaking service depends on the `PlayerProvider` interface instead of directly depending on Python gRPC code. This allows switching between:

- `MockPlayerProvider` for local development;
- `GrpcPlayerProvider` for real integration with the Python Player Service.

---

## Environment variables

### Go Matchmaking Service

Create `services/matchmaking-service/.env`:

```env
HTTP_PORT=8080
PLAYER_SERVICE_GRPC_ADDR=localhost:50051
DATABASE_URL=postgres://postgres:admin@localhost:5433/pusha_matchmaking_db?sslmode=disable
```

Adjust the PostgreSQL port if your local container uses another port.

### Python Player Service

Create `services/player-service/.env` from `.env.example` and configure PostgreSQL and gRPC settings, for example:

```env
POSTGRES_USER=player
POSTGRES_PASSWORD=change-me
POSTGRES_HOST=localhost
POSTGRES_PORT=5434
POSTGRES_DB=player_db

GRPC_HOST=0.0.0.0
GRPC_PORT=50051

HTTP_HOST=0.0.0.0
HTTP_PORT=8000
```

### Golang Matchmaking Service

The Go Matchmaking Service uses environment variables from `services/matchmaking-service/.env`.
Create it from the example file:
```env
HTTP_PORT=8080
PLAYER_SERVICE_GRPC_ADDR=localhost:50051
DATABASE_URL=postgres://postgres:admin@localhost:5433/pusha_matchmaking_db?sslmode=disable
```
---

## Running locally

### 1. Start PostgreSQL for Matchmaking Service

```powershell
docker run --name pusha-matchmaking-postgres `
  -e POSTGRES_USER=postgres `
  -e POSTGRES_PASSWORD=admin `
  -e POSTGRES_DB=pusha_matchmaking_db `
  -p 5433:5432 `
  -d postgres:16
```

Apply Go service migration:

```powershell
cd services/matchmaking-service
Get-Content migrations/001_init_matchmaking.sql | docker exec -i pusha-matchmaking-postgres psql -U postgres -d pusha_matchmaking_db
```

### 2. Start PostgreSQL for Player Service

```powershell
docker run --name pusha-player-postgres `
  -e POSTGRES_USER=player `
  -e POSTGRES_PASSWORD=change-me `
  -e POSTGRES_DB=player_db `
  -p 5434:5432 `
  -d postgres:16
```

### 3. Prepare Python Player Service

```powershell
cd services/player-service
py -3.12 -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m alembic upgrade head
python -m scripts.seed_grpc_data
python -m app.main
```

The seed script prints player UUIDs. Use one of them as `author_id` when creating a matchmaking request.

### 4. Start Go Matchmaking Service

In another terminal:

```powershell
cd services/matchmaking-service
go run ./cmd/server
```

The API should be available at:

```text
http://localhost:8080
```

---

## Swagger UI

If Swaggo is configured and docs are generated, run the Go service and open:

```text
http://localhost:8080/swagger/index.html
```

To regenerate Swagger docs:

```powershell
cd services/matchmaking-service
swag init -g cmd/server/main.go -o docs --parseInternal
```

If `swag` is not in PATH on Windows:

```powershell
& "$env:USERPROFILE\go\bin\swag.exe" init -g cmd/server/main.go -o docs --parseInternal
```

---

## REST API Overview

The project has REST APIs in **both services**.

### Matchmaking Service REST API — Go

Base URL:

```text
http://localhost:8080
```

Swagger UI:

```text
http://localhost:8080/swagger/index.html
```

| Method | Endpoint                                               | Description                                 |
| ------ | ------------------------------------------------------ | ------------------------------------------- |
| `GET`  | `/health`                                              | Check Go service health                     |
| `POST` | `/api/v1/matchmaking/requests`                         | Create a matchmaking request                |
| `GET`  | `/api/v1/matchmaking/requests/{request_id}`            | Get matchmaking request by ID               |
| `GET`  | `/api/v1/players/{player_id}/matchmaking/requests`     | Get requests created by player              |
| `POST` | `/api/v1/matchmaking/requests/{request_id}/search`     | Search, filter and score candidates         |
| `GET`  | `/api/v1/matchmaking/requests/{request_id}/candidates` | Get stored candidates for request           |
| `POST` | `/api/v1/matchmaking/requests/{request_id}/group`      | Create match group from selected candidates |

### Player Service REST API — Python

Base URL:

```text
http://localhost:8000
```

FastAPI documentation:

```text
http://localhost:8000/docs
```

| Method  | Endpoint                                       | Description                                 |
| ------- | ---------------------------------------------- | ------------------------------------------- |
| `GET`   | `/health`                                      | Check Python service health                 |
| `POST`  | `/api/v1/players`                              | Create player with initial Valorant profile |
| `GET`   | `/api/v1/players/{player_id}`                  | Get player with Valorant profile            |
| `PATCH` | `/api/v1/players/{player_id}/valorant-profile` | Update Valorant profile data                |
| `PATCH` | `/api/v1/players/{player_id}/status`           | Update player availability status           |
| `POST`  | `/api/v1/players/{target_player_id}/reviews`   | Create teammate review for player           |
| `GET`   | `/api/v1/players/{player_id}/reviews`          | List reviews received by player             |


## Example full flow

### 1. Create matchmaking request

```http
POST /api/v1/matchmaking/requests
```

```json
{
  "author_id": "2b3f8f29-1c42-56ce-8988-24210ae29b7e",
  "min_rank": "GOLD_1",
  "max_rank": "PLATINUM_3",
  "required_player_status": "READY_TO_PLAY",
  "min_teammate_rating": 4.0,
  "region": "EU",
  "required_roles": ["CONTROLLER", "SENTINEL"],
  "needed_players": 4,
  "strategy": "BALANCED"
}
```

### 2. Search candidates

```http
POST /api/v1/matchmaking/requests/{request_id}/search
```

This calls the Python Player Service via gRPC, filters candidates, calculates scores and stores the result.

### 3. Get candidates

```http
GET /api/v1/matchmaking/requests/{request_id}/candidates
```

### 4. Create match group

```http
POST /api/v1/matchmaking/requests/{request_id}/group
```

```json
{
  "selected_candidate_ids": [
    "a2456ecb-3be7-54a1-9f1c-f3f434083dc8",
    "c753bad6-9640-540f-b53c-084f365970f3"
  ]
}
```

After group creation, the matchmaking request status becomes `COMPLETED`.

---

## Testing

### Go tests

```powershell
cd services/matchmaking-service
go test ./...
go test ./... -cover
```

The Go service contains tests for:

- request validation;
- scoring strategies;
- candidate specifications;
- application error responses;
- HTTP handlers;
- gRPC-to-domain mapping.

### Python tests

```powershell
cd services/player-service
.\.venv\Scripts\activate
python -m pytest
```

---

## Notes

- The Go service owns matchmaking requests, candidates and match groups.
- The Python service owns players, Valorant profiles and teammate reviews.
- Candidate scoring is performed in Go.
- Player data is retrieved from Python via gRPC.
- The system is designed so that the Go service can use a mock provider or a real gRPC provider without changing the main matchmaking flow.
