import aiosqlite
from pathlib import Path
from typing import Optional
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: Optional[str] = None):
        if db_path:
            self.db_path = db_path
        else:
            # Extract path from sqlite URL
            db_url = settings.database_url
            if db_url.startswith("sqlite:///"):
                self.db_path = db_url.replace("sqlite:///", "")
            else:
                self.db_path = "./database/listings.db"

        # Ensure database directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self._initialized = False

    async def initialize(self):
        """Initialize database with schema"""
        if self._initialized:
            return

        schema_path = Path(__file__).parent.parent.parent.parent / "database" / "schema.sql"

        if not schema_path.exists():
            logger.error(f"Schema file not found at {schema_path}")
            raise FileNotFoundError(f"Schema file not found at {schema_path}")

        async with aiosqlite.connect(self.db_path) as db:
            with open(schema_path, 'r') as f:
                schema = f.read()

            await db.executescript(schema)
            await db.commit()

        self._initialized = True
        logger.info(f"Database initialized at {self.db_path}")

    async def get_connection(self):
        """Get database connection"""
        if not self._initialized:
            await self.initialize()

        conn = await aiosqlite.connect(self.db_path)
        conn.row_factory = aiosqlite.Row
        return conn


# Global database instance
db = Database()
