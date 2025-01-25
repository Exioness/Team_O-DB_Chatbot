from contextlib import asynccontextmanager
from typing import AsyncGenerator
import psycopg_pool
from psycopg import AsyncConnection

from app.core.config import settings

class AuthDatabasePool:
    def __init__(self):
        self.pool = None

    async def initialize(self):
        if not self.pool:
            self.pool = psycopg_pool.AsyncConnectionPool(
                conninfo=(
                    f"host={settings.AUTH_DB_HOST} "
                    f"dbname={settings.AUTH_DB_NAME} "
                    f"user={settings.AUTH_DB_USER} "
                    f"password={settings.AUTH_DB_PASSWORD}"
                ),
                min_size=5,
                max_size=20,
                open=False
            )
            await self.pool.open()

    @asynccontextmanager
    async def get_conn(self) -> AsyncGenerator[AsyncConnection, None]:
        if not self.pool:
            await self.initialize()
        async with self.pool.connection() as conn:
            yield conn

    async def close_all(self):
        if self.pool:
            await self.pool.close()

auth_db = AuthDatabasePool()
