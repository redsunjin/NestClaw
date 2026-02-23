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


def _is_enabled(name: str, *, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("utf-8").rstrip("=")


def _auth_error(message: str) -> HTTPException:
    return HTTPException(status_code=401, detail={"error": {"code": "UNAUTHORIZED", "message": message}})


def _split_jwt(token: str) -> tuple[str, str, str]:
    parts = token.split(".")
    if len(parts) != 3:
        raise _auth_error("invalid bearer token format")
    return parts[0], parts[1], parts[2]


def _decode_json_part(value: str) -> dict[str, Any]:
    try:
        return json.loads(_b64url_decode(value).decode("utf-8"))
    except Exception as exc:  # pragma: no cover - defensive
        raise _auth_error(f"invalid jwt part: {exc}") from exc


def _validate_common_claims(payload: dict[str, Any], *, expected_issuer: str | None, expected_audience: str | None) -> None:
    exp = payload.get("exp")
    if exp is not None:
        try:
            if int(exp) < int(time.time()):
                raise _auth_error("expired bearer token")
        except ValueError as exc:
            raise _auth_error("invalid exp in bearer token") from exc

    nbf = payload.get("nbf")
    if nbf is not None:
        try:
            if int(nbf) > int(time.time()):
                raise _auth_error("token not active yet")
        except ValueError as exc:
            raise _auth_error("invalid nbf in bearer token") from exc

    if expected_issuer and payload.get("iss") != expected_issuer:
        raise _auth_error("issuer mismatch")

    if expected_audience:
        aud = payload.get("aud")
        if isinstance(aud, list):
            if expected_audience not in aud:
                raise _auth_error("audience mismatch")
        elif aud != expected_audience:
            raise _auth_error("audience mismatch")


def _decode_local_jwt_hs256(token: str, secret: str) -> dict[str, Any]:
    header_b64, payload_b64, signature_b64 = _split_jwt(token)
    header = _decode_json_part(header_b64)
    payload = _decode_json_part(payload_b64)

    if header.get("alg") != "HS256":
        raise _auth_error("unsupported token alg for local auth")

    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected_sig = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    expected_b64 = _b64url_encode(expected_sig)
    if not hmac.compare_digest(signature_b64, expected_b64):
        raise _auth_error("invalid bearer token signature")

    _validate_common_claims(payload, expected_issuer=None, expected_audience=None)
    return payload


def _load_jwks_from_file(path: str) -> dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.loads(fh.read())
    except FileNotFoundError as exc:
        raise _auth_error(f"jwks file not found: {path}") from exc
    except Exception as exc:  # pragma: no cover - defensive
        raise _auth_error(f"failed to read jwks: {exc}") from exc


def _lookup_jwk(jwks: dict[str, Any], kid: str | None) -> dict[str, Any]:
    keys = jwks.get("keys")
    if not isinstance(keys, list) or not keys:
        raise _auth_error("jwks has no keys")
    if kid:
        for key in keys:
            if key.get("kid") == kid:
                return key
        raise _auth_error("jwks key not found for kid")
    return keys[0]


def _verify_jwk_hs256(header_b64: str, payload_b64: str, signature_b64: str, jwk: dict[str, Any]) -> None:
    if jwk.get("kty") != "oct":
        raise _auth_error("invalid jwk type for hs256")
    encoded_key = jwk.get("k")
    if not isinstance(encoded_key, str):
        raise _auth_error("jwks key missing 'k'")

    secret = _b64url_decode(encoded_key)
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected_sig = hmac.new(secret, signing_input, hashlib.sha256).digest()
    if not hmac.compare_digest(signature_b64, _b64url_encode(expected_sig)):
        raise _auth_error("invalid idp token signature")


def _verify_jwk_rs256(header_b64: str, payload_b64: str, signature_b64: str, jwk: dict[str, Any]) -> None:
    if jwk.get("kty") != "RSA":
        raise _auth_error("invalid jwk type for rs256")
    n_b64 = jwk.get("n")
    e_b64 = jwk.get("e")
    if not isinstance(n_b64, str) or not isinstance(e_b64, str):
        raise _auth_error("jwks rsa key missing n/e")

    try:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding, rsa
    except Exception as exc:  # pragma: no cover - optional dependency
        raise _auth_error("rs256 verification requires cryptography package") from exc

    n = int.from_bytes(_b64url_decode(n_b64), byteorder="big")
    e = int.from_bytes(_b64url_decode(e_b64), byteorder="big")
    public_key = rsa.RSAPublicNumbers(e=e, n=n).public_key()
    signature = _b64url_decode(signature_b64)
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    try:
        public_key.verify(signature, signing_input, padding.PKCS1v15(), hashes.SHA256())
    except Exception as exc:  # pragma: no cover - defensive
        raise _auth_error(f"invalid idp token signature: {exc}") from exc


def _decode_idp_jwt(token: str, *, jwks_path: str, issuer: str | None, audience: str | None) -> dict[str, Any]:
    header_b64, payload_b64, signature_b64 = _split_jwt(token)
    header = _decode_json_part(header_b64)
    payload = _decode_json_part(payload_b64)
    alg = header.get("alg")
    kid = header.get("kid")

    jwks = _load_jwks_from_file(jwks_path)
    jwk = _lookup_jwk(jwks, kid)

    if alg == "HS256":
        _verify_jwk_hs256(header_b64, payload_b64, signature_b64, jwk)
    elif alg == "RS256":
        _verify_jwk_rs256(header_b64, payload_b64, signature_b64, jwk)
    else:
        raise _auth_error(f"unsupported idp token alg: {alg}")

    _validate_common_claims(payload, expected_issuer=issuer, expected_audience=audience)
    return payload


def _claims_to_actor(payload: dict[str, Any], *, role_claim: str, source: str) -> ActorContext:
    sub = str(payload.get("sub") or "").strip()
    role = str(payload.get(role_claim) or "").strip().lower()
    if not sub or role not in VALID_ROLES:
        raise _auth_error("token missing valid sub/role")
    return ActorContext(actor_id=sub, actor_role=role, source=source)


def _resolve_bearer_actor(token: str) -> ActorContext:
    mode = os.getenv("NEWCLAW_AUTH_MODE", "mixed").strip().lower()
    role_claim = os.getenv("NEWCLAW_IDP_ROLE_CLAIM", "role").strip() or "role"
    idp_jwks_path = os.getenv("NEWCLAW_IDP_JWKS_PATH", "").strip()
    idp_issuer = os.getenv("NEWCLAW_IDP_ISSUER", "").strip() or None
    idp_audience = os.getenv("NEWCLAW_IDP_AUDIENCE", "").strip() or None
    local_secret = os.getenv("NEWCLAW_JWT_SECRET", "newclaw-dev-secret-change")

    if mode == "local":
        return _claims_to_actor(_decode_local_jwt_hs256(token, local_secret), role_claim="role", source="jwt")

    if mode == "idp":
        if not idp_jwks_path:
            raise _auth_error("idp mode requires NEWCLAW_IDP_JWKS_PATH")
        return _claims_to_actor(
            _decode_idp_jwt(token, jwks_path=idp_jwks_path, issuer=idp_issuer, audience=idp_audience),
            role_claim=role_claim,
            source="idp",
        )

    # mixed mode: if token issuer matches configured IdP issuer, enforce IdP verification.
    header_b64, payload_b64, _ = _split_jwt(token)
    header = _decode_json_part(header_b64)
    payload = _decode_json_part(payload_b64)
    token_iss = str(payload.get("iss") or "").strip()
    should_try_idp = False
    if idp_jwks_path:
        if idp_issuer:
            should_try_idp = token_iss == idp_issuer
        else:
            should_try_idp = bool(header.get("kid"))

    if should_try_idp:
        return _claims_to_actor(
            _decode_idp_jwt(token, jwks_path=idp_jwks_path, issuer=idp_issuer, audience=idp_audience),
            role_claim=role_claim,
            source="idp",
        )

    return _claims_to_actor(_decode_local_jwt_hs256(token, local_secret), role_claim="role", source="jwt")


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
    sso_token: str | None,
) -> ActorContext:
    auth_mode = os.getenv("NEWCLAW_AUTH_MODE", "mixed").strip().lower()

    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        return _resolve_bearer_actor(token)

    if sso_token:
        idp_jwks_path = os.getenv("NEWCLAW_IDP_JWKS_PATH", "").strip()
        if not idp_jwks_path:
            raise _auth_error("sso token provided but NEWCLAW_IDP_JWKS_PATH is not configured")
        role_claim = os.getenv("NEWCLAW_IDP_ROLE_CLAIM", "role").strip() or "role"
        claims = _decode_idp_jwt(
            sso_token.strip(),
            jwks_path=idp_jwks_path,
            issuer=os.getenv("NEWCLAW_IDP_ISSUER", "").strip() or None,
            audience=os.getenv("NEWCLAW_IDP_AUDIENCE", "").strip() or None,
        )
        return _claims_to_actor(claims, role_claim=role_claim, source="idp")

    if auth_mode == "idp":
        raise _auth_error("idp mode requires token-based authentication")

    if sso_user and sso_role and _is_enabled("NEWCLAW_ALLOW_TRUSTED_SSO_HEADERS", default=False):
        role = sso_role.strip().lower()
        if role not in VALID_ROLES:
            raise _auth_error("invalid sso role")
        return ActorContext(actor_id=sso_user.strip(), actor_role=role, source="sso")

    if actor_id and actor_role and _is_enabled("NEWCLAW_ALLOW_COMPAT_HEADERS", default=True):
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
    sso_token: str | None = Header(default=None, alias="X-SSO-Token"),
) -> ActorContext:
    return resolve_actor_context(authorization, actor_id, actor_role, sso_user, sso_role, sso_token)
