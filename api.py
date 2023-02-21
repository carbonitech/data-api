from fastapi import FastAPI, HTTPException
from data import FRED, ClimatePredictionCenter

app = FastAPI()

### FRED-DATA ###
@app.get("/fred-data")
def get_fred_series_with_calculated_data(series_id: str, fred_api_key: str|None = None):
    fred = FRED(api_key=fred_api_key)
    return fred.data_enriched(series_id)

@app.get("/cdd/cumulative-differences")
def get_cooling_degree_day_cumulative_differences_yoy(states: str):
    states_split = [e.upper() for e in states.split(",")]
    if any(map(lambda e: len(e)!=2 ,states_split)):
        raise HTTPException(
            status_code=400,
            detail="'states' query parameter expects a comma-seperated list of 2-character state identifiers (i.e. 'FL' for 'Florida')"
        )

    cpc = ClimatePredictionCenter(states_split)
    return cpc.cooling_degree_days_diff_yoy()
