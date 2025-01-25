import json
import asyncio
import os
from datetime import datetime
from typing import Dict, List, Any, AsyncGenerator, Optional
from openai import OpenAI
from fastapi import HTTPException
from pathlib import Path

from app.core.config import settings
from app.core.database import db
from app.core.auth_database import auth_db

class ChatService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.system_prompt = self._load_system_prompt()
    
    def _load_system_prompt(self) -> str:
        try:
            path = Path(__file__).parent.parent / "prompt.txt"
            with open(path, "r") as f:
                return f.read().strip()
        except Exception:
            return """You are a helpful SQL assistant. Use the database schema to create accurate queries:
{SCHEMA}"""

    async def get_database_info(self) -> List[Dict[str, Any]]:
        """Get database schema information with column types"""
        async with db.get_conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                tables = await cur.fetchall()
                
                schema_info = []
                for table in tables:
                    await cur.execute("""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_schema = 'public' 
                        AND table_name = %s
                    """, (table[0],))
                    columns = await cur.fetchall()
                    
                    schema_info.append({
                        "table_name": table[0],
                        "columns": [
                            {"name": col[0], "type": col[1]} 
                            for col in columns
                        ]
                    })
                return schema_info

    async def execute_query(self, query: str) -> str:
        """Execute a database query"""
        try:
            async with db.get_conn() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(query)
                    results = await cur.fetchall()
                    return str([dict(zip([col.name for col in cur.description], row)) for row in results])
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Query failed: {str(e)}")

    def _setup_tools(self, database_schema: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Setup tools configuration with data types"""
        schema_string = "\n".join([
            f"Table: {table['table_name']}\n" + "\n".join(
                [f"- {col['name']} ({col['type']})" 
                 for col in table['columns']]
            ) 
            for table in database_schema
        ])
        
        return [{
            "type": "function",
            "function": {
                "name": "ask_database",
                "description": "Use this function to answer database questions.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": f"SQL query using schema:\n{schema_string}",
                        }
                    },
                    "required": ["query"],
                }
            }
        }]

    async def _get_chat_history(self, chat_id: int) -> List[Dict[str, Any]]:
        """Retrieve chat history with roles from database"""
        async with auth_db.get_conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT role, content FROM messages WHERE chat_id = %s ORDER BY created_at",
                    (chat_id,)
                )
                messages = await cur.fetchall()
                return [{"role": msg[0], "content": msg[1]} for msg in messages]

    async def _save_message(self, chat_id: int, content: str, role: str):
        """Save message to database with role"""
        async with auth_db.get_conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO messages (chat_id, role, content) VALUES (%s, %s, %s)",
                    (chat_id, role, content)
                )
                await conn.commit()

    async def process_user_query(self, user_question: str, chat_id: int):
        """Process a user query with history"""
        try:
            database_schema = await self.get_database_info()
            history = await self._get_chat_history(chat_id)
            
            system_message = self.system_prompt.replace(
                "{SCHEMA}", 
                json.dumps(database_schema, indent=2)
            )
            
            messages = [
                {"role": "system", "content": system_message},
                *history,
                {"role": "user", "content": user_question}
            ]
            
            tools = self._setup_tools(database_schema)
            
            response = self.client.chat.completions.create(
                model='gpt-4o-2024-11-20',
                messages=messages,
                tools=tools,
                tool_choice={"type": "function", "function": {"name": "ask_database"}},
                temperature=0.2
            )
            
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            if not tool_calls:
                raise HTTPException(
                    status_code=400,
                    detail="Could not generate valid SQL"
                )

            if tool_calls[0].function.name == 'ask_database':
                query = json.loads(tool_calls[0].function.arguments)['query']
                results = await self.execute_query(query)
                
                messages.extend([
                    response_message,
                    {
                        "role": "tool",
                        "tool_call_id": tool_calls[0].id,
                        "name": tool_calls[0].function.name,
                        "content": results
                    }
                ])

                final_response = self.client.chat.completions.create(
                    model="gpt-4o-2024-11-20",
                    messages=messages
                )
                
                # Save messages with proper roles
                await self._save_message(chat_id, user_question, "user")
                await self._save_message(chat_id, final_response.choices[0].message.content, "assistant")
                
                return {
                    "success": True,
                    "sql_query": query,
                    "query_results": results,
                    "explanation": final_response.choices[0].message.content
                }
                
            raise HTTPException(status_code=400, detail="Query processing failed")
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def process_user_query_stream(self, user_question: str, chat_id: int) -> AsyncGenerator[str, None]:
        """Process query with streaming response"""
        try:
            database_schema = await self.get_database_info()
            history = await self._get_chat_history(chat_id)
            
            system_message = self.system_prompt.replace(
                "{SCHEMA}", 
                json.dumps(database_schema, indent=2)
            )
            
            messages = [
                {"role": "system", "content": system_message},
                *history,
                {"role": "user", "content": user_question}
            ]
            
            tools = self._setup_tools(database_schema)
            
            response = self.client.chat.completions.create(
                model='gpt-4o-2024-11-20',
                messages=messages,
                tools=tools,
                tool_choice={"type": "function", "function": {"name": "ask_database"}},
                temperature=0.2
            )
            
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            if not tool_calls:
                yield "data: " + json.dumps({
                    "type": "error",
                    "content": "Could not generate SQL"
                }) + "\n\n"
                return

            if tool_calls[0].function.name == 'ask_database':
                query = json.loads(tool_calls[0].function.arguments)['query']
                
                yield "data: " + json.dumps({
                    "type": "sql",
                    "content": query
                }) + "\n\n"
                await asyncio.sleep(0.1)

                results = await self.execute_query(query)
                yield "data: " + json.dumps({
                    "type": "results",
                    "content": results
                }) + "\n\n"
                await asyncio.sleep(0.1)
                
                messages.extend([
                    response_message,
                    {
                        "role": "tool",
                        "tool_call_id": tool_calls[0].id,
                        "name": tool_calls[0].function.name,
                        "content": results
                    }
                ])

                final_response = self.client.chat.completions.create(
                    model="gpt-4o-2024-11-20",
                    messages=messages,
                    stream=True
                )
                
                full_response = []
                for chunk in final_response:
                    if chunk.choices[0].delta.content:
                        chunk_content = chunk.choices[0].delta.content
                        full_response.append(chunk_content)
                        yield "data: " + json.dumps({
                            "type": "token",
                            "content": chunk_content
                        }) + "\n\n"
                
                # Save messages with proper roles
                await self._save_message(chat_id, user_question, "user")
                await self._save_message(chat_id, "".join(full_response), "assistant")
                
                yield "data: " + json.dumps({"type": "end"}) + "\n\n"
                
        except Exception as e:
            yield "data: " + json.dumps({
                "type": "error",
                "content": str(e)
            }) + "\n\n"

    async def create_chat(self, user_id: int, title: Optional[str] = None) -> Dict[str, Any]:
        """Create a new chat"""
        try:
            async with auth_db.get_conn() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """
                        INSERT INTO chats (user_id, title)
                        VALUES (%s, %s)
                        RETURNING id, title, created_at
                        """,
                        (user_id, title or "New Chat")
                    )
                    chat = await cur.fetchone()
                    await conn.commit()
                    return {
                        "id": chat[0],
                        "title": chat[1],
                        "created_at": chat[2],
                        "user_id": user_id
                    }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create chat: {str(e)}")

    async def get_user_chats(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all chats for a user"""
        try:
            async with auth_db.get_conn() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        """
                        SELECT id, title, created_at 
                        FROM chats 
                        WHERE user_id = %s 
                        ORDER BY created_at DESC
                        """,
                        (user_id,)
                    )
                    chats = await cur.fetchall()
                    return [{
                        "id": chat[0],
                        "title": chat[1],
                        "created_at": chat[2],
                        "user_id": user_id
                    } for chat in chats]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch chats: {str(e)}")

    async def delete_chat(self, chat_id: int, user_id: int) -> bool:
        """Delete a specific chat"""
        try:
            async with auth_db.get_conn() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        "DELETE FROM chats WHERE id = %s AND user_id = %s",
                        (chat_id, user_id)
                    )
                    await conn.commit()
                    return cur.rowcount > 0
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete chat: {str(e)}")

    async def delete_all_user_chats(self, user_id: int) -> bool:
        """Delete all chats for a user"""
        try:
            async with auth_db.get_conn() as conn:
                async with conn.cursor() as cur:
                    await cur.execute(
                        "DELETE FROM chats WHERE user_id = %s",
                        (user_id,)
                    )
                    await conn.commit()
                    return True
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete chats: {str(e)}")

chat_service = ChatService()