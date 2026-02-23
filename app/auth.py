from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass
from typing import Any

from fastapi import Header, HTTPException


VALID_ROLES = {"requester", "reviewer", "approver", "admin"}


@dataclass(frozen=True)
class ActorContext:
    actor_id: str
    actor_role: str
    source: str


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("utf-8").rstrip("=")


def _auth_error(message: str) -> HTTPException:
    return HTTPException(status_code=401, detail={"error": {"code": "UNAUTHORIZED", "message": message}})


def _decode_jwt_hs256(token: str, secret: str) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3:
        raise _auth_error("invalid bearer token format")

    header_b64, payload_b64, signature_b64 = parts
    try:
        header = json.loads(_b64url_decode(header_b64).decode("utf-8"))
        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    except Exception as exc:  # pragma: no cover - defensive
        raise _auth_error(f"invalid bearer token payload: {exc}") from exc

    if header.get("alg") != "HS256":
        raise _auth_error("unsupported token alg")

    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected_sig = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    expected_b64 = _b64url_encode(expected_sig)
    if not hmac.compare_digest(signature_b64, expected_b64):
        raise _auth_error("invalid bearer token signature")

    exp = payload.get("exp")
    if exp is not None:
        try:
            if int(exp) < int(time.time()):
                raise _auth_error("expired bearer token")
        except ValueError as exc:
            raise _auth_error("invalid exp in bearer token") from exc

    return payload


def issue_dev_jwt(sub: str, role: str, *, expires_in_seconds: int = 3600, secret: str | None = None) -> str:
    if role not in VALID_ROLES:
        raise ValueError(f"unsupported role: {role}")
    secret_value = secret or os.getenv("NEWCLAW_JWT_SECRET", "newclaw-dev-secret-change")
    now = int(time.time())
    payload = {"sub": sub, "role": role, "iat": now, "exp": now + expires_in_seconds}
    header = {"alg": "HS256", "typ": "JWT"}

    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    sig = hmac.new(secret_value.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{header_b64}.{payload_b64}.{_b64url_encode(sig)}"


def resolve_actor_context(
    authorization: str | None,
    actor_id: str | None,
    actor_role: str | None,
    sso_user: str | None,
    sso_role: str | None,
) -> ActorContext:
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        claims = _decode_jwt_hs256(token, os.getenv("NEWCLAW_JWT_SECRET", "newclaw-dev-secret-change"))
        sub = str(claims.get("sub") or "").strip()
        role = str(claims.get("role") or "").strip().lower()
        if not sub or role not in VALID_ROLES:
            raise _auth_error("bearer token missing sub/role")
        return ActorContext(actor_id=sub, actor_role=role, source="jwt")

    if sso_user and sso_role:
        role = sso_role.strip().lower()
        if role not in VALID_ROLES:
            raise _auth_error("invalid sso role")
        return ActorContext(actor_id=sso_user.strip(), actor_role=role, source="sso")

    if actor_id and actor_role:
        role = actor_role.strip().lower()
        if role not in VALID_ROLES:
            raise _auth_error("invalid header role")
        return ActorContext(actor_id=actor_id.strip(), actor_role=role, source="header")

    raise _auth_error("missing authentication context")


def actor_context_dependency(
    authorization: str | None = Header(default=None, alias="Authorization"),
    actor_id: str | None = Header(default=None, alias="X-Actor-Id"),
    actor_role: str | None = Header(default=None, alias="X-Actor-Role"),
    sso_user: str | None = Header(default=None, alias="X-SSO-User"),
    sso_role: str | None = Header(default=None, alias="X-SSO-Role"),
) -> ActorContext:
    return resolve_actor_context(authorization, actor_id, actor_role, sso_user, sso_role)
