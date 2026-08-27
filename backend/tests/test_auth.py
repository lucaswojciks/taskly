"""Integration tests for the authentication feature.

Spec: ``docs/specs/auth.md``.

These tests are written before the production code exists. Every test is
expected to fail because the ``/auth/*`` routes are not registered yet (the app
returns ``404``). That is a valid "red": a collection/import error or a syntax
error would not be.

Token-forging helpers sign with ``TEST_JWT_SECRET``. The implementation step
must make the test environment sign real tokens with this same secret (via the
``JWT_SECRET_KEY`` env var) so the "expired token" test exercises the expiry
path rather than the signature path.
"""

import datetime as dt
from typing import Any

import jwt
from httpx import AsyncClient, Response

TEST_JWT_SECRET = "test-secret-key-for-auth-tests-not-for-production-use"
WRONG_JWT_SECRET = "a-completely-different-secret-also-long-enough-32b"
JWT_ALGORITHM = "HS256"
EXPECTED_TOKEN_TTL_SECONDS = 3600  # spec: ACCESS_TOKEN_EXPIRE_MINUTES = 60

VALID_EMAIL = "alice@example.com"
VALID_PASSWORD = "s3cure-pass"
A_USER_ID = "11111111-1111-1111-1111-111111111111"


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
async def register(
    client: AsyncClient,
    email: str = VALID_EMAIL,
    password: str = VALID_PASSWORD,
) -> Response:
    return await client.post("/auth/register", json={"email": email, "password": password})


async def login(
    client: AsyncClient,
    email: str = VALID_EMAIL,
    password: str = VALID_PASSWORD,
) -> Response:
    return await client.post("/auth/login", json={"email": email, "password": password})


async def obtain_token(
    client: AsyncClient,
    email: str = VALID_EMAIL,
    password: str = VALID_PASSWORD,
) -> str:
    await register(client, email, password)
    response = await login(client, email, password)
    assert response.status_code == 200, f"login failed: {response.status_code} {response.text}"
    token = response.json()["access_token"]
    assert isinstance(token, str)
    return token


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def make_token(
    *,
    secret: str = TEST_JWT_SECRET,
    sub: str = A_USER_ID,
    token_type: str = "access",
    issued_offset_seconds: int = 0,
    expires_offset_seconds: int = EXPECTED_TOKEN_TTL_SECONDS,
) -> str:
    now = dt.datetime.now(dt.UTC)
    claims: dict[str, Any] = {
        "sub": sub,
        "type": token_type,
        "iat": now + dt.timedelta(seconds=issued_offset_seconds),
        "exp": now + dt.timedelta(seconds=expires_offset_seconds),
    }
    return jwt.encode(claims, secret, algorithm=JWT_ALGORITHM)


# --------------------------------------------------------------------------- #
# registration
# --------------------------------------------------------------------------- #
async def test_register_valid_returns_201_without_password_hash(client: AsyncClient) -> None:
    response = await register(client)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == VALID_EMAIL
    assert "id" in body
    assert "created_at" in body
    assert "hashed_password" not in body
    assert "password" not in body


async def test_register_duplicate_email_returns_409(client: AsyncClient) -> None:
    first = await register(client)
    assert first.status_code == 201

    second = await register(client)
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "email_already_exists"


async def test_register_invalid_email_returns_422(client: AsyncClient) -> None:
    response = await register(client, email="not-an-email")

    assert response.status_code == 422


async def test_register_short_password_returns_422(client: AsyncClient) -> None:
    response = await register(client, password="short")  # 5 characters, < 8

    assert response.status_code == 422


async def test_register_uppercase_email_is_normalized_and_collides(client: AsyncClient) -> None:
    created = await register(client, email="Alice@Example.com")
    assert created.status_code == 201
    # persisted lower-cased
    assert created.json()["email"] == "alice@example.com"

    collision = await register(client, email="ALICE@EXAMPLE.COM")
    assert collision.status_code == 409
    assert collision.json()["error"]["code"] == "email_already_exists"


# --------------------------------------------------------------------------- #
# login
# --------------------------------------------------------------------------- #
async def test_login_valid_returns_200_with_token(client: AsyncClient) -> None:
    await register(client)

    response = await login(client)

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["access_token"], str) and body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == EXPECTED_TOKEN_TTL_SECONDS


async def test_login_wrong_password_returns_401(client: AsyncClient) -> None:
    await register(client)

    response = await login(client, password="not-the-password")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_credentials"


async def test_login_unknown_email_matches_wrong_password_response(client: AsyncClient) -> None:
    await register(client, email=VALID_EMAIL, password=VALID_PASSWORD)

    wrong_password = await login(client, email=VALID_EMAIL, password="not-the-password")
    unknown_email = await login(client, email="ghost@example.com", password=VALID_PASSWORD)

    assert wrong_password.status_code == 401
    assert unknown_email.status_code == 401
    assert wrong_password.json()["error"]["code"] == "invalid_credentials"
    # identical body: no way to tell "email exists" from "wrong password"
    assert wrong_password.json() == unknown_email.json()


async def test_login_uppercase_email_is_normalized(client: AsyncClient) -> None:
    await register(client, email="alice@example.com")

    response = await login(client, email="ALICE@example.com")

    assert response.status_code == 200
    assert isinstance(response.json()["access_token"], str)


# --------------------------------------------------------------------------- #
# protected route: GET /auth/me
# --------------------------------------------------------------------------- #
async def test_me_with_valid_token_returns_current_user(client: AsyncClient) -> None:
    token = await obtain_token(client)

    response = await client.get("/auth/me", headers=auth_header(token))

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == VALID_EMAIL
    assert "id" in body
    assert "created_at" in body
    assert "hashed_password" not in body


async def test_me_without_authorization_header_returns_401(client: AsyncClient) -> None:
    response = await client.get("/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "not_authenticated"


async def test_me_with_malformed_token_returns_401(client: AsyncClient) -> None:
    response = await client.get("/auth/me", headers=auth_header("this-is-not-a-jwt"))

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "not_authenticated"


async def test_me_with_invalid_signature_returns_401(client: AsyncClient) -> None:
    forged = make_token(secret=WRONG_JWT_SECRET)

    response = await client.get("/auth/me", headers=auth_header(forged))

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "not_authenticated"


async def test_me_with_expired_token_returns_401(client: AsyncClient) -> None:
    expired = make_token(issued_offset_seconds=-7200, expires_offset_seconds=-3600)

    response = await client.get("/auth/me", headers=auth_header(expired))

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "not_authenticated"
