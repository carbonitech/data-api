"""
Routes for retrieving customer-related database info
"""

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

customers = APIRouter(prefix="/customers", tags=["Customers"])

@customers.get("")
async def all_customers():
    with open('./data/ga_customers.csv') as db_file:
        return PlainTextResponse(db_file.read())