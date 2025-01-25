from contextlib import asynccontextmanager
from typing import AsyncGenerator
import psycopg_pool
from psycopg import AsyncConnection
from psycopg.rows import dict_row

from app.core.config import settings

class DatabasePool:
    def __init__(self):
        self.pool = None

    async def initialize(self):
        """Initialize the connection pool"""
        if not self.pool:
            self.pool = psycopg_pool.AsyncConnectionPool(
                conninfo=(
                    f"host={settings.DB_HOST} "
                    f"dbname={settings.DB_NAME} "
                    f"user={settings.DB_USER} "
                    f"password={settings.DB_PASSWORD}"
                ),
                min_size=5,
                max_size=20,
                open=False # Don't open in constructor
            )
        await self.pool.open() # Explicitly open the pool

    @asynccontextmanager
    async def get_conn(self) -> AsyncGenerator[AsyncConnection, None]:
        """Get a database connection from the pool"""
        if not self.pool:
            await self.initialize()
        async with self.pool.connection() as conn:
            yield conn

    async def close_all(self):
        """Close all connections"""
        if self.pool:
            await self.pool.close()

db = DatabasePool()