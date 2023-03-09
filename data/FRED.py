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

    def sep_meta_from_obs_and_prep_obs_for_pandas(self, data: dict) -> tuple[dict,dict]:
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
        return metadata, df_data

    async def get_data(self, series_id: str) -> dict:
        response = requests.get(self.FULL_URL.format(series_id=series_id))
        data: dict = response.json()
        return data

    async def data_enriched(self, data: pd.DataFrame) -> dict:
        data = data.merge(rolling_12(data["value"].interpolate()), left_index=True, right_index=True)
        data = data.merge(rolling_3(data["value"].interpolate()), left_index=True, right_index=True)
        data = data.fillna(self.NAN_CHAR)
        return data.astype(str)
    
    async def fred_series(self, series_id: str) -> dict:
        data = await self.get_data(series_id)
        metadata, df_data = self.sep_meta_from_obs_and_prep_obs_for_pandas(data)
        observations_df = pd.DataFrame.from_dict(df_data, orient="index")
        observations_df = await self.data_enriched(observations_df)
        # recombine metadata and observervations as a list of dicts, moving the date index into a key-value pair in the observation
        result = metadata | df_to_list_objs_w_date_indx_as_attr(observations_df, "observations")
        return result
    
    async def housing_inventory_by_state(self, state: str) -> dict:
        """The National Association of Realtors defines Housing Inventory as
            'Inventory is calculated monthly by taking a count of the number of
            active listings and pending sales on the last day of the month'
            
            Source: https://www.nar.realtor/blogs/economists-outlook/inventory-and-months-supply#:~:text=When%20a%20seller%20lists%20a,last%20day%20of%20the%20month."""
        base_series_id_active = "ACTLISCOU"
        base_series_id_pending = "PENLISCOU"

        active_listings = await self.get_data(base_series_id_active + state)
        pending_listings = await self.get_data(base_series_id_pending + state)

        meta_active, obs_active = self.sep_meta_from_obs_and_prep_obs_for_pandas(active_listings)
        meta_pending, obs_pending = self.sep_meta_from_obs_and_prep_obs_for_pandas(pending_listings)
        assert meta_active == meta_pending, "metadata dicts are different between active and pending series"

        df_active = pd.DataFrame.from_dict(obs_active, orient="index")
        df_pending = pd.DataFrame.from_dict(obs_pending, orient="index")

        inventory = df_active.merge(df_pending["value"], left_index=True, right_index=True,
                                    suffixes=("_a", "_p"))
        inventory["value"] = inventory["value_a"] + inventory["value_p"]
        inventory = inventory.drop(columns=["value_a", "value_p"])
        inventory = await self.data_enriched(inventory)
        # recombine metadata and observervations as a list of dicts, moving the date index into a key-value pair in the observation
        result = meta_active | df_to_list_objs_w_date_indx_as_attr(inventory, "observations")
        return result
            