import os


def normalize_database_url(url: str) -> str:
    """
    Use psycopg 3 for PostgreSQL while accepting Neon-style connection URLs.
    Non-PostgreSQL URLs are left untouched for local tests.
    """
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://"):]

    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://"):]

    return url


def get_database_url() -> str:
    value = os.getenv("DATABASE_URL")
    if not value:
        raise RuntimeError(
            "DATABASE_URL is not set. Configure the Neon pooled PostgreSQL "
            "connection string before using --persist-db or Alembic."
        )

    return normalize_database_url(value)
