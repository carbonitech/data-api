""""""

from fastapi import APIRouter, HTTPException
from data.data.FRED import FRED

fred = APIRouter(prefix="/fred-data", tags=["FRED"])

def valid_states_input(states: list[str]) -> bool:
    if any(map(lambda e: len(e)!=2 ,states)):
        raise HTTPException(
            status_code=400,
            detail="'states' query parameter expects a comma-seperated list of 2-character state identifiers (i.e. 'FL' for 'Florida')"
        )
    return True

### FRED-DATA ###
@fred.get("")
async def get_fred_series_with_calculated_data(series_id: str, fred_api_key: str|None = None):
    fred = FRED(api_key=fred_api_key)
    return await fred.fred_series(series_id)

@fred.get("/housing-inventory")
async def housing_inventory_by_state(state: str, fred_api_key: str|None = None):
    fred = FRED(api_key=fred_api_key)
    return await fred.housing_inventory_by_state(state)
