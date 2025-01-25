from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class MessageResponse(BaseModel):
    id: int
    chat_id: int
    role: str 
    content: str
    created_at: datetime

class QueryRequest(BaseModel):
    question: str
    chat_id: int  

class QueryResponse(BaseModel):
    success: bool
    sql_query: str
    query_results: str
    explanation: str

class SchemaResponse(BaseModel):
    schema: List[Dict[str, Any]]

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str

class ChatCreate(BaseModel):
    title: Optional[str] = None
    initial_message: Optional[str] = None

class ChatResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    user_id: int