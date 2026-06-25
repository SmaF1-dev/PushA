import json
import unittest
from collections.abc import Awaitable, Callable
from typing import Any
from uuid import UUID, uuid4

from fastapi import FastAPI

from app.api.dependencies import (
    get_player_service,
    get_profile_service,
    get_review_service,
)
from app.config import AppEnvironment, Settings
from app.main import create_app
from app.repositories.exceptions import DuplicateRiotIdError
from app.services import PlayerService, ProfileService, ReviewService
from tests.fakes import (
    FakePlayerRepository,
    FakeProfileRepository,
    FakeReviewRepository,
    FakeTransactionManager,
)


AsgiMessage = dict[str, Any]
AsgiReceive = Callable[[], Awaitable[AsgiMessage]]
AsgiSend = Callable[[AsgiMessage], Awaitable[None]]


async def request_app(
    app: FastAPI,
    method: str,
    path: str,
    *,
    json_body: dict[str, Any] | None = None,
    query: str = "",
) -> tuple[int, dict[str, Any]]:
    """Send one HTTP request directly through the ASGI interface.

    :param app: FastAPI application under test.
    :param method: HTTP request method.
    :param path: Request path without a query string.
    :param json_body: Optional JSON request object.
    :param query: Raw query string without the leading question mark.
    :returns: HTTP status and decoded JSON response body.
    """
    body = json.dumps(json_body).encode() if json_body is not None else b""
    messages: list[AsgiMessage] = []
    request_sent = False

    async def receive() -> AsgiMessage:
        """Provide the request body to the ASGI application.

        :returns: ASGI request or disconnect message.
        """
        nonlocal request_sent
        if request_sent:
            return {"type": "http.disconnect"}
        request_sent = True
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message: AsgiMessage) -> None:
        """Collect one ASGI response message.

        :param message: Response event emitted by the application.
        :returns: ``None``.
        """
        messages.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": query.encode(),
        "root_path": "",
        "headers": [(b"content-type", b"application/json")],
        "client": ("test-client", 1234),
        "server": ("test-server", 80),
        "state": {},
    }
    await app(scope, receive, send)

    start = next(message for message in messages if message["type"] == "http.response.start")
    response_body = b"".join(
        message.get("body", b"")
        for message in messages
        if message["type"] == "http.response.body"
    )
    return start["status"], json.loads(response_body)


def test_settings() -> Settings:
    """Build isolated settings without reading the service ``.env`` file.

    :returns: Valid settings suitable for API unit tests.
    """
    return Settings(
        _env_file=None,
        app_env=AppEnvironment.TEST,
        postgres_user="test",
        postgres_password="test",
        postgres_host="localhost",
        postgres_db="test",
    )


class ConcurrentConflictPlayerRepository(FakePlayerRepository):
    """Simulate another transaction claiming a Riot ID after the pre-check."""

    async def add(self, player):
        """Raise the persistence-level duplicate error during insertion.

        :param player: Player accepted by the initial availability check.
        :raises DuplicateRiotIdError: Always, to imitate a concurrent insert.
        """
        raise DuplicateRiotIdError(player.riot_id)


class RestApiTests(unittest.IsolatedAsyncioTestCase):
    """Verify the public REST contract with in-memory repositories."""

    def setUp(self) -> None:
        """Compose an application with test doubles for persistence.

        :returns: ``None``.
        """
        self.players = FakePlayerRepository()
        self.profiles = FakeProfileRepository()
        self.reviews = FakeReviewRepository()
        self.transaction = FakeTransactionManager()

        self.player_service = PlayerService(
            self.players,
            self.profiles,
            self.transaction,
        )
        self.profile_service = ProfileService(self.profiles, self.transaction)
        self.review_service = ReviewService(
            self.players,
            self.profiles,
            self.reviews,
            self.transaction,
        )

        self.app = create_app(test_settings())
        self.app.dependency_overrides[get_player_service] = lambda: self.player_service
        self.app.dependency_overrides[get_profile_service] = lambda: self.profile_service
        self.app.dependency_overrides[get_review_service] = lambda: self.review_service

    async def create_player(self, *, riot_id: str) -> tuple[int, dict[str, Any]]:
        """Create a player through the public API.

        :param riot_id: Unique Riot identifier used for the request.
        :returns: HTTP status and decoded response.
        """
        return await request_app(
            self.app,
            "POST",
            "/api/v1/players",
            json_body={
                "nickname": "Sage Main",
                "riot_id": riot_id,
                "region": "eu",
                "current_rank": "GOLD_2",
                "main_roles": ["SENTINEL"],
            },
        )

    async def test_health_endpoint(self) -> None:
        """Return service liveness without touching the database."""
        status, body = await request_app(self.app, "GET", "/health")

        self.assertEqual(status, 200)
        self.assertEqual(body, {"status": "ok", "service": "player-service"})

    async def test_create_and_get_player(self) -> None:
        """Create and retrieve a player with their profile."""
        created_status, created = await self.create_player(riot_id="Sage#EU")
        player_id = created["player"]["id"]
        get_status, received = await request_app(
            self.app,
            "GET",
            f"/api/v1/players/{player_id}",
        )

        self.assertEqual(created_status, 201)
        self.assertEqual(get_status, 200)
        self.assertEqual(received, created)
        self.assertEqual(received["valorant_profile"]["region"], "EU")

    async def test_duplicate_riot_id_returns_conflict(self) -> None:
        """Translate a duplicate Riot ID into HTTP 409."""
        await self.create_player(riot_id="Taken#EU")
        status, body = await self.create_player(riot_id="Taken#EU")

        self.assertEqual(status, 409)
        self.assertIn("already registered", body["detail"])

    async def test_concurrent_riot_id_conflict_returns_conflict(self) -> None:
        """Translate a uniqueness race detected during database insertion."""
        racing_transaction = FakeTransactionManager()
        racing_service = PlayerService(
            ConcurrentConflictPlayerRepository(),
            self.profiles,
            racing_transaction,
        )
        self.app.dependency_overrides[get_player_service] = lambda: racing_service

        status, body = await self.create_player(riot_id="Race#EU")

        self.assertEqual(status, 409)
        self.assertIn("already registered", body["detail"])
        self.assertEqual(racing_transaction.commits, 0)
        self.assertEqual(racing_transaction.rollbacks, 1)

    async def test_invalid_request_returns_structured_422(self) -> None:
        """Expose request validation errors in a stable schema."""
        status, body = await request_app(
            self.app,
            "POST",
            "/api/v1/players",
            json_body={"nickname": ""},
        )

        self.assertEqual(status, 422)
        self.assertEqual(body["detail"], "request validation failed")
        self.assertTrue(body["errors"])

    async def test_missing_player_returns_not_found(self) -> None:
        """Translate a missing aggregate into HTTP 404."""
        status, body = await request_app(
            self.app,
            "GET",
            f"/api/v1/players/{uuid4()}",
        )

        self.assertEqual(status, 404)
        self.assertIn("was not found", body["detail"])

    async def test_update_profile_and_status(self) -> None:
        """Apply both supported profile PATCH operations."""
        _, created = await self.create_player(riot_id="Patch#EU")
        player_id = created["player"]["id"]

        profile_status, profile = await request_app(
            self.app,
            "PATCH",
            f"/api/v1/players/{player_id}/valorant-profile",
            json_body={
                "region": "na",
                "current_rank": "PLATINUM_1",
                "main_roles": ["CONTROLLER", "INITIATOR"],
            },
        )
        status_status, status_body = await request_app(
            self.app,
            "PATCH",
            f"/api/v1/players/{player_id}/status",
            json_body={"status": "READY_TO_PLAY"},
        )

        self.assertEqual(profile_status, 200)
        self.assertEqual(profile["region"], "NA")
        self.assertEqual(profile["current_rank"], "PLATINUM_1")
        self.assertEqual(status_status, 200)
        self.assertEqual(status_body["status"], "READY_TO_PLAY")

    async def test_create_and_list_reviews(self) -> None:
        """Create a review, recalculate rating, and return a page."""
        _, reviewer = await self.create_player(riot_id="Reviewer#EU")
        _, target = await self.create_player(riot_id="Target#EU")
        reviewer_id = reviewer["player"]["id"]
        target_id = target["player"]["id"]

        create_status, review = await request_app(
            self.app,
            "POST",
            f"/api/v1/players/{target_id}/reviews",
            json_body={
                "reviewer_id": reviewer_id,
                "rating": 5,
                "comment": "Calm comms",
            },
        )
        list_status, page = await request_app(
            self.app,
            "GET",
            f"/api/v1/players/{target_id}/reviews",
            query="limit=10&offset=0",
        )
        profile = await self.profiles.get_by_player_id(UUID(target_id))

        self.assertEqual(create_status, 201)
        self.assertEqual(list_status, 200)
        self.assertEqual(page["items"], [review])
        self.assertEqual(page["limit"], 10)
        self.assertIsNotNone(profile)
        self.assertEqual(profile.teammate_rating, 5.0)
        self.assertEqual(profile.reviews_count, 1)

    async def test_self_review_returns_domain_validation_error(self) -> None:
        """Translate the domain self-review rule into HTTP 422."""
        _, player = await self.create_player(riot_id="Solo#EU")
        player_id = player["player"]["id"]

        status, body = await request_app(
            self.app,
            "POST",
            f"/api/v1/players/{player_id}/reviews",
            json_body={"reviewer_id": player_id, "rating": 5},
        )

        self.assertEqual(status, 422)
        self.assertIn("cannot review themselves", body["detail"])

    async def test_openapi_contains_complete_public_contract(self) -> None:
        """Publish all specified routes in OpenAPI."""
        status, schema = await request_app(self.app, "GET", "/openapi.json")

        self.assertEqual(status, 200)
        self.assertEqual(
            set(schema["paths"]),
            {
                "/api/v1/players",
                "/api/v1/players/{player_id}",
                "/api/v1/players/{player_id}/valorant-profile",
                "/api/v1/players/{player_id}/status",
                "/api/v1/players/{target_player_id}/reviews",
                "/api/v1/players/{player_id}/reviews",
                "/health",
            },
        )


if __name__ == "__main__":
    unittest.main()
