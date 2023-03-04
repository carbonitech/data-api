""""""

from fastapi import APIRouter
from data.FRED import FRED

fred = APIRouter(prefix="/fred-data", tags=["FRED"])

### FRED-DATA ###
@fred.get("")
async def get_fred_series_with_calculated_data(series_id: str, fred_api_key: str|None = None):
    fred = FRED(api_key=fred_api_key)
    return await fred.data_enriched(series_id)
