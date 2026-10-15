from app.db.session import ensure_database


def upgrade_database() -> None:
    ensure_database()
