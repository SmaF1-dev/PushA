import logging

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.db.integrity import RIOT_ID_UNIQUE_CONSTRAINT, find_constraint_name
from app.domain import DomainError
from app.services import (
    PlayerNotFoundError,
    ProfileNotFoundError,
    RiotIdAlreadyExistsError,
)


logger = logging.getLogger(__name__)


async def handle_not_found(
    request: Request,
    exception: PlayerNotFoundError | ProfileNotFoundError,
) -> JSONResponse:
    """Convert missing player or profile errors into HTTP 404.

    :param request: Request that produced the error.
    :param exception: Expected application not-found error.
    :returns: JSON response with status 404.
    """
    del request
    return JSONResponse(status_code=404, content={"detail": str(exception)})


async def handle_riot_id_conflict(
    request: Request,
    exception: RiotIdAlreadyExistsError,
) -> JSONResponse:
    """Convert a duplicate Riot ID into HTTP 409.

    :param request: Request that produced the error.
    :param exception: Duplicate Riot ID application error.
    :returns: JSON response with status 409.
    """
    del request
    return JSONResponse(status_code=409, content={"detail": str(exception)})


async def handle_domain_error(
    request: Request,
    exception: DomainError,
) -> JSONResponse:
    """Convert a domain-invariant violation into HTTP 422.

    :param request: Request that produced the error.
    :param exception: Domain validation error.
    :returns: JSON response with status 422.
    """
    del request
    return JSONResponse(status_code=422, content={"detail": str(exception)})


async def handle_request_validation_error(
    request: Request,
    exception: RequestValidationError,
) -> JSONResponse:
    """Return a stable body for FastAPI request-validation failures.

    :param request: Request containing invalid input.
    :param exception: FastAPI validation error.
    :returns: JSON response with status 422 and structured validation details.
    """
    del request
    return JSONResponse(
        status_code=422,
        content={
            "detail": "request validation failed",
            "errors": jsonable_encoder(exception.errors()),
        },
    )


async def handle_integrity_error(
    request: Request,
    exception: IntegrityError,
) -> JSONResponse:
    """Handle a database constraint race without leaking database details.

    :param request: Request that produced the database violation.
    :param exception: SQLAlchemy integrity error.
    :returns: HTTP 409 for a duplicate Riot ID, otherwise HTTP 500.
    """
    del request
    if find_constraint_name(exception) == RIOT_ID_UNIQUE_CONSTRAINT:
        return JSONResponse(
            status_code=409,
            content={"detail": "Riot ID is already registered"},
        )

    logger.error(
        "Unhandled database integrity error",
        exc_info=(type(exception), exception, exception.__traceback__),
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "internal server error"},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all Player Service exception handlers.

    :param app: FastAPI application receiving the handlers.
    :returns: ``None``.
    """
    app.add_exception_handler(PlayerNotFoundError, handle_not_found)
    app.add_exception_handler(ProfileNotFoundError, handle_not_found)
    app.add_exception_handler(RiotIdAlreadyExistsError, handle_riot_id_conflict)
    app.add_exception_handler(DomainError, handle_domain_error)
    app.add_exception_handler(RequestValidationError, handle_request_validation_error)
    app.add_exception_handler(IntegrityError, handle_integrity_error)
