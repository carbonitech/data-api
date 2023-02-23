from fastapi import FastAPI, HTTPException
from data import FRED, ClimatePredictionCenter
import datetime

app = FastAPI()

### FRED-DATA ###
@app.get("/fred-data")
def get_fred_series_with_calculated_data(series_id: str, fred_api_key: str|None = None):
    fred = FRED(api_key=fred_api_key)
    return fred.data_enriched(series_id)

@app.get("/cdd/cumulative-differences")
def get_cooling_degree_day_cumulative_differences_yoy(states: str, base_year: int|None = None):
    states_split = [e.upper() for e in states.split(",")]
    current_year = datetime.datetime.now().year
    if any(map(lambda e: len(e)!=2 ,states_split)):
        raise HTTPException(
            status_code=400,
            detail="'states' query parameter expects a comma-seperated list of 2-character state identifiers (i.e. 'FL' for 'Florida')"
        )
    if base_year:
        if base_year < 0:
            base_year = abs(base_year)
        if len(str(base_year)) != 4:
            raise HTTPException(400, "Base year should be a 4 digit number representing a year (i.e. 2023)")
        elif base_year > current_year:
            raise HTTPException(400, f"Cannot pull data for a year beyond the current year: {current_year}")


    cpc = ClimatePredictionCenter(states_split, base_year)
    return cpc.cooling_degree_days_diff_yoy()
