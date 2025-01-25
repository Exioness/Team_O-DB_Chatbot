from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from typing import List

from app.core.config import settings
from app.core.security import create_access_token
from app.api.deps import get_current_user
from app.services.auth_service import auth_service
from app.services.chat_service import chat_service
from app.api.schemas import (
    UserCreate, UserResponse, Token, ChatCreate, 
    ChatResponse, QueryRequest, SchemaResponse, MessageResponse
)
from app.core.auth_database import auth_db

router = APIRouter()

@router.get("/schema", response_model=SchemaResponse)
async def get_schema():
    """Get database schema"""
    schema = await chat_service.get_database_info()
    return {"schema": schema}

@router.post("/query")
async def process_query(request: QueryRequest):
    """Process query with streaming"""
    return StreamingResponse(
        chat_service.process_user_query_stream(request.question, request.chat_id),
        media_type='text/event-stream'
    )

@router.get("/chats/{chat_id}/messages", response_model=List[MessageResponse])
async def get_chat_messages(
    chat_id: int,
    current_user: dict = Depends(get_current_user)
):
    async with auth_db.get_conn() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT m.id, m.chat_id, m.role, m.content, m.created_at 
                FROM messages m
                JOIN chats c ON m.chat_id = c.id
                WHERE c.user_id = %s AND m.chat_id = %s
                ORDER BY m.created_at
                """,
                (current_user["id"], chat_id)
            )
            messages = await cur.fetchall()
            return [{
                "id": msg[0],
                "chat_id": msg[1],
                "role": msg[2],
                "content": msg[3],
                "created_at": msg[4]
            } for msg in messages]

@router.post("/auth/signup", response_model=UserResponse)
async def signup(user_data: UserCreate):
    return await auth_service.create_user(user_data)

@router.post("/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": str(user["id"])},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    return current_user

@router.post("/chats", response_model=ChatResponse)
async def create_chat(
    chat_data: ChatCreate,
    current_user: dict = Depends(get_current_user)
):
    return await chat_service.create_chat(current_user["id"], chat_data.title)

@router.get("/chats", response_model=List[ChatResponse])
async def get_chats(current_user: dict = Depends(get_current_user)):
    return await chat_service.get_user_chats(current_user["id"])

@router.delete("/chats/{chat_id}")
async def delete_chat(
    chat_id: int,
    current_user: dict = Depends(get_current_user)
):
    if await chat_service.delete_chat(chat_id, current_user["id"]):
        return {"message": "Chat deleted successfully"}
    raise HTTPException(status_code=404, detail="Chat not found")

@router.delete("/chats")
async def delete_all_chats(current_user: dict = Depends(get_current_user)):
    await chat_service.delete_all_user_chats(current_user["id"])
    return {"message": "All chats deleted successfully"}