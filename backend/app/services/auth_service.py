from typing import Optional
from datetime import timedelta
from fastapi import HTTPException, status
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.config import settings
from app.core.auth_database import auth_db
from app.api.schemas import UserCreate, UserResponse

class AuthService:
    async def create_user(self, user_data: UserCreate) -> UserResponse:
        async with auth_db.get_conn() as conn:
            async with conn.cursor() as cur:
                # Check if user exists
                await cur.execute(
                    "SELECT id FROM users WHERE username = %s OR email = %s",
                    (user_data.username, user_data.email)
                )
                if await cur.fetchone():
                    raise HTTPException(
                        status_code=400,
                        detail="Username or email already registered"
                    )
                
                # Create new user
                hashed_password = get_password_hash(user_data.password)
                await cur.execute(
                    """
                    INSERT INTO users (username, email, password_hash)
                    VALUES (%s, %s, %s) RETURNING id, username, email
                    """,
                    (user_data.username, user_data.email, hashed_password)
                )
                user = await cur.fetchone()
                await conn.commit()
                
                return UserResponse(
                    id=user[0],
                    username=user[1],
                    email=user[2]
                )

    async def authenticate_user(self, username: str, password: str) -> Optional[dict]:
        async with auth_db.get_conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT id, username, email, password_hash FROM users WHERE username = %s",
                    (username,)
                )
                user = await cur.fetchone()
                
                if not user or not verify_password(password, user[3]):
                    return None
                
                return {
                    "id": user[0],
                    "username": user[1],
                    "email": user[2]
                }

    async def get_user_by_id(self, user_id: int) -> Optional[dict]:
        async with auth_db.get_conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT id, username, email FROM users WHERE id = %s",
                    (user_id,)
                )
                user = await cur.fetchone()
                
                if not user:
                    return None
                
                return {
                    "id": user[0],
                    "username": user[1],
                    "email": user[2]
                }

auth_service = AuthService()
