"""sqlite-vec connection loading shared by application and Alembic engines."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def load_sqlite_vec_extension(dbapi_connection: Any) -> bool:
    """Load sqlite-vec into a DBAPI connection and always re-disable extension loading."""
    try:
        import sqlite_vec

        dbapi_connection.enable_load_extension(True)
        try:
            sqlite_vec.load(dbapi_connection)
        finally:
            dbapi_connection.enable_load_extension(False)
        return True
    except Exception as err:
        logger.warning("Failed to load sqlite-vec extension: %s", err)
        return False
