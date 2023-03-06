"""
    Interface for the Climate Prediction Center.
    Degree Day raw data is updated daily and available in pipe-delimited format
"""

import pandas as pd
import datetime
import calendar

from data import df_to_list_objs_w_date_indx_as_attr, cumulative_differences


class ClimatePredictionCenter:
    BASE_URL = "https://ftp.cpc.ncep.noaa.gov/htdocs/degree_days/weighted/daily_data/"
    LATEST = "latest/"
    NORMALS = "climatology/1981-2010/"
    STATES_COOLING = "StatesCONUS.Cooling.txt"
    STATES_HEATING = "StatesCONUS.Heating.txt"
    CLIMATE_DIVS_COOLING = "ClimateDivisions.Cooling.txt"
    CLIMATE_DIVS_HEATING = "ClimateDivisions.Heating.txt"
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
            data = await self.match_climate_ids_to_states(data)
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
            data = await self.match_climate_ids_to_states(data)
        data = data.T
        data = data.loc[:,(self.states_selected)]
        data = data.reset_index()
        data["ref_date_index"] = data["index"] + pd.DateOffset(years=1)
        data = data.set_index("ref_date_index").drop(columns="index", level=0 if self.climate_divs else None)
        return data


    async def get_normals_daily(self) -> pd.DataFrame:
        data = pd.read_csv(self.full_url_base_normals(), skiprows=3, delimiter="|")
        data = data.set_index('Region')
        ref_year = self.base_year if self.base_year else self.current_year

        if not calendar.isleap(ref_year):
            data = data.loc[:,~data.columns.str.endswith('0229')]

        data.columns = [pd.to_datetime(str(ref_year) + date, format=r"%Y%m%d") for date in data.columns]
        if self.climate_divs:
            data = await self.match_climate_ids_to_states(data)
        data = data.T
        data = data.loc[:,(self.states_selected)]
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

    async def get_climate_div_county_state_map(self) -> pd.DataFrame:
        return pd.read_csv("./db/region_id_mapping.csv")

    async def match_climate_ids_to_states(self, data: pd.DataFrame) -> pd.DataFrame:
        data = data.reset_index()
        reference: pd.DataFrame = await self.get_climate_div_county_state_map()
        data = data.merge(reference, left_on="Region", right_on="Region ID")
        # formatting the region column so it shows the region name with the region ID in parentheses
        data["Region"] = data["Name"].str.cat(data['Region'].astype(str).str[-2:].apply(lambda x: f"({x})"), sep=" ")
        data = data.drop(columns=["CD", "Name", "Region ID"])\
            .set_index(["ST", "Region"])
        return data

    def formatted_output(self, dataframe: pd.DataFrame) -> dict:
        self.length = len(dataframe)
        return {"metadata": self.metadata()} | df_to_list_objs_w_date_indx_as_attr(dataframe, "observations")
    
