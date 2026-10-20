"""Create or update the administrator from environment variables."""

import sys

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.auth import require_admin_seed_config, seed_admin_user


def main() -> None:
    settings = get_settings()
    try:
        require_admin_seed_config(settings.admin_email, settings.admin_password)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    with SessionLocal() as session:
        result = seed_admin_user(session, settings.admin_email, settings.admin_password)
    print(f"Admin {result}")


if __name__ == "__main__":
    main()
