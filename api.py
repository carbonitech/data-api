from fastapi import FastAPI, HTTPException
from data import FRED, ClimatePredictionCenter
import datetime

app = FastAPI()

def valid_states_input(states: list[str]) -> bool:
    if any(map(lambda e: len(e)!=2 ,states)):
        raise HTTPException(
            status_code=400,
            detail="'states' query parameter expects a comma-seperated list of 2-character state identifiers (i.e. 'FL' for 'Florida')"
        )
    return True
    
def valid_year_input(input_year: int) -> bool:
    current_year = datetime.datetime.now().year
    if len(str(input_year)) != 4:
        raise HTTPException(400, "Base year should be a 4 digit number representing a year (i.e. 2023)")
    elif input_year > current_year:
        raise HTTPException(400, f"Cannot pull data for a year beyond the current year: {current_year}")

    return True

### FRED-DATA ###
@app.get("/fred-data")
async def get_fred_series_with_calculated_data(series_id: str, fred_api_key: str|None = None):
    fred = FRED(api_key=fred_api_key)
    return await fred.data_enriched(series_id)

## COOLING DEGREE DAYS (CDD) ##
@app.get("/cdd")
async def get_cooling_degree_days_raw(states: str, year: int|None = None):
    states_split = [e.upper() for e in states.split(",")]
    assert valid_states_input(states_split)
    if year:
        if year < 0:
            year = abs(year)
        assert valid_year_input(year)

    cpc = ClimatePredictionCenter(states_split, year)
    return await cpc.cooling_degree_days()


@app.get("/cdd/cumulative")
async def get_cumulative_cdd(states: str, normals: bool=False, base_year: int|None = None):
    states_split = [e.upper() for e in states.split(",")]
    assert valid_states_input(states_split)
    if base_year:
        if base_year < 0:
            base_year = abs(base_year)
        assert valid_year_input(base_year)
    cpc = ClimatePredictionCenter(states_split, base_year)
    return await cpc.cooling_degree_days_cumulative(normals)


@app.get("/cdd/cumulative-differences")
async def get_cooling_degree_day_cumulative_differences_yoy(states: str, base_year: int|None = None):
    states_split = [e.upper() for e in states.split(",")]
    assert valid_states_input(states_split)

    if base_year:
        if base_year < 0:
            base_year = abs(base_year)
        assert valid_year_input(base_year)

    cpc = ClimatePredictionCenter(states_split, base_year)
    return await cpc.cooling_degree_days_diff_yoy()
