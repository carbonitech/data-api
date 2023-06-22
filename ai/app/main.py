from fastapi import APIRouter, Depends
from ai.auth.auth import authenticate_auth0_token
from ai.app.resources.files import files
from ai.app.resources.chat import chat

app = APIRouter(prefix='/ai', tags=['AI Chatbot'])
app.include_router(files, dependencies=[Depends(authenticate_auth0_token)])
app.include_router(chat)

