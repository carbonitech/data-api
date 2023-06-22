from fastapi import APIRouter
from ai.app.resources.files import files
from ai.app.resources.chat import chat

app = APIRouter(prefix='/ai', tags=['AI Chatbot'])
app.include_router(files)
app.include_router(chat)

