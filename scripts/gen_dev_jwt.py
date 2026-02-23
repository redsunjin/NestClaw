#!/usr/bin/env python3
from __future__ import annotations

import argparse

from app.auth import issue_dev_jwt


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a development JWT for new_claw API")
    parser.add_argument("--sub", required=True, help="subject/user id")
    parser.add_argument("--role", required=True, choices=["requester", "reviewer", "approver", "admin"])
    parser.add_argument("--expires", type=int, default=3600, help="expiration in seconds (default: 3600)")
    args = parser.parse_args()

    token = issue_dev_jwt(args.sub, args.role, expires_in_seconds=args.expires)
    print(token)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
