from ai.app.resources.dependencies import get_ai
from ai.ai.ai import AI
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

chat = APIRouter(prefix='/chat')

class Query(BaseModel):
    query: str

class AIResponse(BaseModel):
    query: str
    response: str

@chat.post('')
async def send_query(query: Query, ai: AI=Depends(get_ai)) -> AIResponse:
    # NOTE: since OpenAI switched to pre-payment, and I haven't set it
    #       up yet, this service is not going to work
    raise HTTPException(status_code=503)
    query_txt = query.query
    gpt_response = ai.ask_model(query=query_txt)
    return AIResponse(query=query.query, response=gpt_response)
