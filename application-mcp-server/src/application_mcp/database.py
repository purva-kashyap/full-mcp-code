"""User-specific database helpers for MCP tools"""
import re
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .db_connection import get_async_session
from .exceptions import ValidationError


EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_email(email: str) -> str:
    normalized_email = (email or "").strip()
    if not normalized_email:
        raise ValidationError("email is required", field="email")
    if not EMAIL_REGEX.match(normalized_email):
        raise ValidationError("Invalid email format", field="email")
    return normalized_email


def _validate_limit(limit: int) -> int:
    if limit <= 0:
        raise ValidationError("limit must be positive", field="limit")
    if limit > 1000:
        raise ValidationError("limit must be <= 1000", field="limit")
    return limit


async def fetch_db_users(email: str, limit: int = 100) -> list[dict[str, Any]]:
    """Fetch users from users table filtered by email."""
    safe_email = _validate_email(email)
    safe_limit = _validate_limit(limit)
    try:
        async with get_async_session() as session:
            result = await session.execute(
                text("SELECT * FROM users WHERE email = :email LIMIT :limit"),
                {"email": safe_email, "limit": safe_limit}
            )
            rows = result.fetchall()
            return [{key: value for key, value in row._mapping.items()} for row in rows]
    except SQLAlchemyError as exc:
        raise ValidationError(
            "Failed to fetch users from PostgreSQL",
            details={"email": safe_email, "db_error": str(exc)},
        ) from exc
