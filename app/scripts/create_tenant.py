"""
CLI: register a new tenant.

Usage:
    python -m app.scripts.create_tenant "Shop X"
    python -m app.scripts.create_tenant "Shop X" --env test
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from typing import Literal, cast

from app.core.logging import get_logger
from app.infrastructure.db.session import AsyncSessionLocal
from app.schemas.tenant import TenantCreate
from app.services.tenant_service import TenantService

logger = get_logger(__name__)


async def _run(name: str, environment: str) -> int:
    """Create the tenant, print result. Return exit code."""
    request = TenantCreate(name=name)

    async with AsyncSessionLocal() as session:
        try:
            service = TenantService()
            result = await service.register(
                session,
                request,
                environment=cast(Literal["live", "test"], environment),
            )
            await session.commit()
        except Exception as exc:
            await session.rollback()
            print(f"❌ Failed: {exc}", file=sys.stderr)
            return 1

    print()
    print("✅ Tenant created")
    print(f"   id:           {result.tenant.id}")
    print(f"   name:         {result.tenant.name}")
    print(f"   prefix:       {result.tenant.api_key_prefix}")
    print()
    print(f"   API key:      {result.api_key}")
    print()
    print("⚠️  Store this API key securely. It will NOT be shown again.")
    print()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Register a new tenant.",
    )
    parser.add_argument("name", help="Human-readable tenant name.")
    parser.add_argument(
        "--env",
        choices=["live", "test"],
        default="live",
        help="Environment prefix for the API key (default: live).",
    )
    args = parser.parse_args()

    return asyncio.run(_run(args.name, args.env))


if __name__ == "__main__":
    sys.exit(main())
