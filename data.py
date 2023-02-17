from os import getenv
from dotenv import load_dotenv
import requests
import pandas as pd
import numpy as np

load_dotenv()

API_KEY = getenv("FRED_API_KEY")
NAN_CHAR = '.'

ROOT_URL = 'https://api.stlouisfed.org/fred'
SERIES_URL = ROOT_URL + "/series/observations?series_id={series_id}&file_type=json"
API_PARAMETER = f'&api_key={API_KEY}'
FULL_URL = SERIES_URL + API_PARAMETER 


def rolling_12(data: pd.Series) -> pd.DataFrame:
    rolling_12 = data.rolling(12).sum()
    rolling_12.name = "rolling_12_month_total"
    rolling_12_pct = (rolling_12 / rolling_12.shift(12)) - 1
    rolling_12_pct.name = "rolling_12_12_pct"
    return pd.merge(rolling_12,rolling_12_pct, left_index=True, right_index=True)
    

def rolling_3(data: pd.Series) -> pd.DataFrame:
    rolling_3 = data.rolling(3).sum()
    rolling_3.name = "rolling_3_month_total"
    rolling_3_pct = (rolling_3 / rolling_3.shift(12)) - 1
    rolling_3_pct.name = "rolling_3_12_pct"
    return pd.merge(rolling_3,rolling_3_pct, left_index=True, right_index=True)


def fred_data_enriched(series_id: str):
    response = requests.get(FULL_URL.format(series_id=series_id))
    data: dict = response.json()
    metadata = {k:v for k,v in data.items() if k != "observations"}
    observations: list[dict] = data["observations"]
    def convert_values(observation: dict) -> dict:
        value = observation.get("value")
        observation["value"] = float(value) if value != NAN_CHAR else np.nan
        return observation
    observations = list(map(convert_values, observations))
    df_data = {
        pd.to_datetime(observation.pop("date"), format=r'%Y-%m-%d'): observation 
        for observation in observations
    }
    observations_df = pd.DataFrame.from_dict(df_data, orient="index")
    observations_df = observations_df.merge(rolling_12(observations_df["value"]), left_index=True, right_index=True)
    observations_df = observations_df.merge(rolling_3(observations_df["value"]), left_index=True, right_index=True)
    observations_df = observations_df.fillna('.')
    observations_df = observations_df.astype(str)
    # recombine metadata and observervations as a list of dicts, moving the date index into a key-value pair in the observation
    result = metadata | {"observations": [
            {"date": str(i.date())} | v 
            for i, v in observations_df.to_dict(orient="index").items()
            ]
        }
    return result

