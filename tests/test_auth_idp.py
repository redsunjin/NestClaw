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


if __name__ == "__main__":
    unittest.main()
