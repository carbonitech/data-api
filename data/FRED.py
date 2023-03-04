"""Interface for the FRED API"""
from os import getenv
from dotenv import load_dotenv
import requests
import pandas as pd
import numpy as np

from data import df_to_list_objs_w_date_indx_as_attr, rolling_12, rolling_3

load_dotenv()

class FRED:

    NAN_CHAR = '.'
    def __init__(self, api_key: str|None = None):
        if not api_key:
            api_key = getenv('FRED_API_KEY')    # temporary until testing of API with front end dev is complete
        ROOT_URL = 'https://api.stlouisfed.org/fred'
        SERIES_URL = ROOT_URL + "/series/observations?series_id={series_id}&file_type=json"
        API_PARAMETER = f'&api_key={api_key}'
        self.FULL_URL = SERIES_URL + API_PARAMETER    

    async def get_data(self, series_id: str) -> dict:
        response = requests.get(self.FULL_URL.format(series_id=series_id))
        data: dict = response.json()
        return data

    async def data_enriched(self, series_id: str) -> dict:
        data = await self.get_data(series_id)
        metadata = {k:v for k,v in data.items() if k != "observations"}
        observations: list[dict] = data["observations"]
        def convert_values(observation: dict) -> dict:
            value = observation.get("value")
            observation["value"] = float(value) if value != self.NAN_CHAR else np.nan
            return observation
        observations = list(map(convert_values, observations))
        df_data = {
            pd.to_datetime(observation.pop("date"), format=r'%Y-%m-%d'): observation 
            for observation in observations
        }
        observations_df = pd.DataFrame.from_dict(df_data, orient="index")
        observations_df = observations_df.merge(rolling_12(observations_df["value"].interpolate()), left_index=True, right_index=True)
        observations_df = observations_df.merge(rolling_3(observations_df["value"].interpolate()), left_index=True, right_index=True)
        observations_df = observations_df.fillna(self.NAN_CHAR)
        observations_df = observations_df.astype(str)
        # recombine metadata and observervations as a list of dicts, moving the date index into a key-value pair in the observation
        result = metadata | df_to_list_objs_w_date_indx_as_attr(observations_df, "observations")
        return result