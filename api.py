from fastapi import FastAPI
from data import fred_data_enriched

app = FastAPI()

### FRED-DATA ###
@app.get("/fred-data")
def get_fred_series_with_caluculated_data(series_id: str):
    return fred_data_enriched(series_id)