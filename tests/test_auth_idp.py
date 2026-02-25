from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import tempfile
import time
import unittest

try:
    from app.auth import issue_dev_jwt, resolve_actor_context
except Exception as exc:  # pragma: no cover - environment dependent
    issue_dev_jwt = None
    resolve_actor_context = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


def _b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("utf-8").rstrip("=")


def _sign_hs256(token_header: dict, token_payload: dict, secret: str) -> str:
    header = _b64url(json.dumps(token_header, separators=(",", ":")).encode("utf-8"))
    payload = _b64url(json.dumps(token_payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header}.{payload}".encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{header}.{payload}.{_b64url(signature)}"


@unittest.skipIf(resolve_actor_context is None, f"auth dependencies unavailable: {IMPORT_ERROR}")
class TestAuthIdP(unittest.TestCase):
    def setUp(self) -> None:
        self._env = dict(os.environ)

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._env)

    def test_idp_token_via_sso_header(self) -> None:
        secret = "idp-shared-secret"
        jwks = {
            "keys": [
                {
                    "kid": "kid-1",
                    "kty": "oct",
                    "alg": "HS256",
                    "k": _b64url(secret.encode("utf-8")),
                }
            ]
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            fh.write(json.dumps(jwks))
            jwks_path = fh.name
        self.addCleanup(lambda: os.path.exists(jwks_path) and os.unlink(jwks_path))

        token = _sign_hs256(
            {"alg": "HS256", "typ": "JWT", "kid": "kid-1"},
            {
                "sub": "idp_user",
                "role": "approver",
                "iss": "https://idp.example",
                "aud": "new_claw",
                "exp": int(time.time()) + 600,
            },
            secret,
        )

        os.environ["NEWCLAW_IDP_JWKS_PATH"] = jwks_path
        os.environ["NEWCLAW_IDP_ISSUER"] = "https://idp.example"
        os.environ["NEWCLAW_IDP_AUDIENCE"] = "new_claw"

        actor = resolve_actor_context(None, None, None, None, None, token)
        self.assertEqual(actor.actor_id, "idp_user")
        self.assertEqual(actor.actor_role, "approver")
        self.assertEqual(actor.source, "idp")

    def test_mixed_mode_keeps_local_jwt(self) -> None:
        assert issue_dev_jwt is not None
        token = issue_dev_jwt("local_user", "requester", expires_in_seconds=600)
        actor = resolve_actor_context(f"Bearer {token}", None, None, None, None, None)
        self.assertEqual(actor.actor_id, "local_user")
        self.assertEqual(actor.actor_role, "requester")
        self.assertEqual(actor.source, "jwt")

    def test_idp_mode_rejects_header_only_auth(self) -> None:
        os.environ["NEWCLAW_AUTH_MODE"] = "idp"
        os.environ["NEWCLAW_ALLOW_COMPAT_HEADERS"] = "1"

        with self.assertRaises(Exception) as ctx:
            resolve_actor_context(None, "user1", "requester", None, None, None)

        self.assertEqual(getattr(ctx.exception, "status_code", None), 401)

    def test_jwks_rotation_accepts_new_kid(self) -> None:
        old_secret = "idp-secret-old"
        new_secret = "idp-secret-new"
        jwks = {
            "keys": [
                {"kid": "kid-old", "kty": "oct", "alg": "HS256", "k": _b64url(old_secret.encode("utf-8"))},
                {"kid": "kid-new", "kty": "oct", "alg": "HS256", "k": _b64url(new_secret.encode("utf-8"))},
            ]
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            fh.write(json.dumps(jwks))
            jwks_path = fh.name
        self.addCleanup(lambda: os.path.exists(jwks_path) and os.unlink(jwks_path))

        os.environ["NEWCLAW_IDP_JWKS_PATH"] = jwks_path
        os.environ["NEWCLAW_IDP_ISSUER"] = "https://idp.example"
        os.environ["NEWCLAW_IDP_AUDIENCE"] = "new_claw"

        token_new = _sign_hs256(
            {"alg": "HS256", "typ": "JWT", "kid": "kid-new"},
            {
                "sub": "idp_rotated_user",
                "role": "reviewer",
                "iss": "https://idp.example",
                "aud": "new_claw",
                "exp": int(time.time()) + 600,
            },
            new_secret,
        )
        actor = resolve_actor_context(None, None, None, None, None, token_new)
        self.assertEqual(actor.actor_id, "idp_rotated_user")
        self.assertEqual(actor.actor_role, "reviewer")
        self.assertEqual(actor.source, "idp")

    def test_jwks_rotation_rejects_removed_key(self) -> None:
        old_secret = "idp-secret-old"
        new_secret = "idp-secret-new"
        jwks_initial = {
            "keys": [
                {"kid": "kid-old", "kty": "oct", "alg": "HS256", "k": _b64url(old_secret.encode("utf-8"))},
                {"kid": "kid-new", "kty": "oct", "alg": "HS256", "k": _b64url(new_secret.encode("utf-8"))},
            ]
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            fh.write(json.dumps(jwks_initial))
            jwks_path = fh.name
        self.addCleanup(lambda: os.path.exists(jwks_path) and os.unlink(jwks_path))

        os.environ["NEWCLAW_IDP_JWKS_PATH"] = jwks_path
        os.environ["NEWCLAW_IDP_ISSUER"] = "https://idp.example"
        os.environ["NEWCLAW_IDP_AUDIENCE"] = "new_claw"

        token_old = _sign_hs256(
            {"alg": "HS256", "typ": "JWT", "kid": "kid-old"},
            {
                "sub": "idp_old_user",
                "role": "approver",
                "iss": "https://idp.example",
                "aud": "new_claw",
                "exp": int(time.time()) + 600,
            },
            old_secret,
        )
        token_new = _sign_hs256(
            {"alg": "HS256", "typ": "JWT", "kid": "kid-new"},
            {
                "sub": "idp_new_user",
                "role": "approver",
                "iss": "https://idp.example",
                "aud": "new_claw",
                "exp": int(time.time()) + 600,
            },
            new_secret,
        )

        actor_before_rotation = resolve_actor_context(None, None, None, None, None, token_old)
        self.assertEqual(actor_before_rotation.actor_id, "idp_old_user")

        jwks_rotated = {
            "keys": [
                {"kid": "kid-new", "kty": "oct", "alg": "HS256", "k": _b64url(new_secret.encode("utf-8"))},
            ]
        }
        with open(jwks_path, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(jwks_rotated))

        with self.assertRaises(Exception) as old_ctx:
            resolve_actor_context(None, None, None, None, None, token_old)
        self.assertEqual(getattr(old_ctx.exception, "status_code", None), 401)

        actor_after_rotation = resolve_actor_context(None, None, None, None, None, token_new)
        self.assertEqual(actor_after_rotation.actor_id, "idp_new_user")
        self.assertEqual(actor_after_rotation.actor_role, "approver")
        self.assertEqual(actor_after_rotation.source, "idp")


if __name__ == "__main__":
    unittest.main()
