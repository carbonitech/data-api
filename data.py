from os import getenv
from dotenv import load_dotenv
import requests
import pandas as pd
import numpy as np
import datetime
import calendar

load_dotenv()

class FRED:
    """Interface for the FRED API"""

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


class ClimatePredictionCenter:
    """
    Interface for the Climate Prediction Center.
    Degree Day raw data is updated daily and available in pipe-delimited format
    """
    BASE_URL = "https://ftp.cpc.ncep.noaa.gov/htdocs/degree_days/weighted/daily_data/"
    LATEST = "latest/"
    NORMALS = "climatology/1981-2010/"
    STATES_COOLING = "StatesCONUS.Cooling.txt"
    CLIMATE_DIVS_COOLING = "ClimateDivisions.Cooling.txt"

    PRIOR_YEAR = str((datetime.datetime.now() - datetime.timedelta(weeks=52)).year) + "/"


    def __init__(self, states_selected: list, base_year: int=None, climate_divisions: bool=False) -> None:
        self.states_selected = states_selected
        self.base_year = base_year
        self.climate_divs = climate_divisions
        self.current_year = datetime.datetime.now().year
        self.length = 0
        self._raw = True
        self._normals = False
        self._differences = False
        self._cumulative = False
        if base_year:
            self.prior_year = base_year - 1
        else:
            self.prior_year = self.current_year - 1


    def metadata(self) -> dict:
        if self.base_year:
            base_year = self.base_year
        else:
            base_year = self.current_year
        result = {"length": self.length, "base_year": base_year}
        response_data = []
        if self._raw:
            return result | {"response_data": "raw"}
        
        if self._normals:
            response_data.append("normals")
        if self._cumulative:
            response_data.append("cumulative")
        if self._differences:
            response_data.append("differences")
            result |= {"comparison_year": self.prior_year}

        return result | {"response_data": ', '.join(response_data)}

    def get_climate_div_county_state_map(self) -> pd.DataFrame:
        """
        retrieves the full county-state mapping to climave division codes
        but cuts the table down to the codes and states, deduped
        """
        data = pd.read_csv("./db/county_clim_divs.csv")
        data["state_climate_division_id"] = data["CLIMDIV_ID"].astype(str).str[:-2]
        data["sub_division_id"] = data["CLIMDIV_ID"].astype(str).str[-2:]
        data = data.loc[:, ["CLIMDIV_ID", "STATE_CODE", "sub_division_id"]].drop_duplicates()
        return data

    def full_url_base_daily(self) -> str:
        if self.base_year:
            result = self.BASE_URL + str(self.base_year) + '/'
        else:
            result = self.BASE_URL + self.LATEST

        if self.climate_divs:
            result += self.CLIMATE_DIVS_COOLING
        else:
            result += self.STATES_COOLING

        return result


    def full_url_comparison_year(self) -> str:
        result =  self.BASE_URL + str(self.prior_year) + '/'
        if self.climate_divs:
            result += self.CLIMATE_DIVS_COOLING
        else:
            result += self.STATES_COOLING
        return result
    

    def full_url_base_normals(self) -> str:
        result = self.BASE_URL + self.NORMALS
        if self.climate_divs:
            result += self.CLIMATE_DIVS_COOLING
        else:
            result += self.STATES_COOLING
        return result


    async def get_current_daily(self) -> pd.DataFrame:
        data = pd.read_csv(self.full_url_base_daily(), skiprows=3, delimiter="|")
        data = data.set_index('Region')
        first_observation_year = int(data.columns.to_list()[0][:4])

        if first_observation_year == self.prior_year:
            # edge case for latest data pulling the year prior at the beginning of the new year
            self.prior_year -= 1

        data.columns = [pd.to_datetime(date, format=r"%Y%m%d") for date in data.columns]
        if self.climate_divs:
            data = data.reset_index()
            reference = self.get_climate_div_county_state_map()
            reference["CLIMDIV_ID"] = reference["CLIMDIV_ID"].astype(int)
            print(data)
            data = data.merge(reference, left_on=data["Region"], right_on="CLIMDIV_ID")\
                .drop(columns=["CLIMDIV_ID", "Region"])\
                .set_index(["STATE_CODE", "sub_division_id"])
        data = data.T
        data = data.loc[:,(self.states_selected)]
        return data


    async def get_prior_year_daily(self) -> pd.DataFrame:
        data = pd.read_csv(self.full_url_comparison_year(), skiprows=3, delimiter="|")
        data = data.set_index('Region')
        first_observation_year = int(data.columns.to_list()[0][:4])

        if calendar.isleap(first_observation_year):
            data = data.loc[:,~data.columns.str.endswith('0229')]

        data.columns = [pd.to_datetime(date, format=r"%Y%m%d") for date in data.columns]
        if self.climate_divs:
            data = data.reset_index()
            reference = self.get_climate_div_county_state_map()
            reference["CLIMDIV_ID"] = reference["CLIMDIV_ID"].astype(int)
            data = data.merge(reference, left_on=data["Region"], right_on="CLIMDIV_ID")\
                .drop(columns=["CLIMDIV_ID", "Region"])\
                .set_index(["STATE_CODE", "sub_division_id"])
        data = data.T
        data = data.loc[:,(self.states_selected)]
        data = data.reset_index()
        data["ref_date_index"] = data["index"] + pd.DateOffset(years=1)
        data = data.set_index("ref_date_index").drop(columns="index")
        return data


    async def get_normals_daily(self) -> pd.DataFrame:
        data = pd.read_csv(self.full_url_base_normals(), skiprows=3, delimiter="|")
        data = data.set_index('Region')
        ref_year = self.base_year if self.base_year else self.current_year

        if not calendar.isleap(ref_year):
            data = data.loc[:,~data.columns.str.endswith('0229')]

        data.columns = [pd.to_datetime(str(ref_year) + date, format=r"%Y%m%d") for date in data.columns]
        data = data.T
        data = data.loc[:,data.columns.isin(self.states_selected)]
        self._normals = True
        return data


    async def cooling_degree_days_diff_yoy(self) -> dict:
        current_year_obs = await self.get_current_daily()
        prior_year_obs = await self.get_prior_year_daily()
        cum_diffs_df = cumulative_differences(current_year_obs, prior_year_obs)
        if not self.climate_divs:   # BUG: Totals, if I keep them, should apply by date, summing the average of the climate divisions
            cum_diffs_df["total"] = cum_diffs_df.apply(sum, axis=1)
        self._cumulative = True
        self._differences = True
        self._raw = False
        return self.formatted_output(cum_diffs_df)


    async def cooling_degree_days_cumulative(self, normals: bool):
        if normals:
            observations = await self.get_normals_daily()
        else:
            observations = await self.get_current_daily()
        self._cumulative = True
        self._raw = False
        return self.formatted_output(observations.cumsum())

    async def cooling_degree_days(self) -> dict:
        df = await self.get_current_daily()
        return self.formatted_output(df)


    def formatted_output(self, dataframe: pd.DataFrame) -> dict:
        self.length = len(dataframe)
        return {"metadata": self.metadata()} | df_to_list_objs_w_date_indx_as_attr(dataframe, "observations")


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

def cumulative_differences(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    return (df1 - df2).cumsum().dropna()

def df_to_list_objs_w_date_indx_as_attr(df: pd.DataFrame, top_lvl_key: str) -> dict[str,list]:
    """
    the dataframe provided is broken out into a list of objects, in which the index is moved into each object
    returns the list as a value to a dictionary, under the key provided in the arg `top_lvl_key`
    """
    df_dict = df.to_dict(orient="index")
    df_dict_exploded_multi_index: dict[datetime.datetime, dict] = {}
    match list(df_dict.get(list(df_dict)[0]))[0]:
        case (k1, k2):
            delevel_keys = True
        case _:
            delevel_keys = False

    if delevel_keys:
        for date, row in df_dict.items():
            row: dict
            df_dict_exploded_multi_index[date] = {}
            for multi_key, value in row.items():
                state, subd_code = multi_key
                if not df_dict_exploded_multi_index[date].get(state):
                    df_dict_exploded_multi_index[date][state] = {subd_code: value}
                else:
                    df_dict_exploded_multi_index[date][state].update({subd_code: value})

        df_dict = df_dict_exploded_multi_index

    return {top_lvl_key: [{"date": str(i.date())} | v for i, v in df_dict.items()]}
    
