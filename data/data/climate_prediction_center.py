"""
Interface for the Climate Prediction Center.
Degree Day raw data is updated daily and available in pipe-delimited format
"""

from typing import Literal
import pandas as pd
import datetime
import calendar
from fastapi import HTTPException

from data.data import df_to_list_objs_w_date_indx_as_attr, cumulative_differences

Mode = Literal["heating", "cooling"]


class InvalidState(Exception): ...


class InvalidYear(Exception): ...


def init_cpc(
    states: str = None,
    base_year: int = None,
    climate_divisions: bool = False,
    mode: Mode = None,
) -> "ClimatePredictionCenter":
    try:
        return ClimatePredictionCenter(states, base_year, climate_divisions, mode)
    except (InvalidYear, InvalidState) as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise e


class ClimatePredictionCenter:
    BASE_URL = "https://ftp.cpc.ncep.noaa.gov/htdocs/degree_days/weighted/daily_data/"
    LATEST = "latest/"
    NORMALS = "climatology/1981-2010/"
    STATES_COOLING = "StatesCONUS.Cooling.txt"
    STATES_HEATING = "StatesCONUS.Heating.txt"
    CLIMATE_DIVS_COOLING = "ClimateDivisions.Cooling.txt"
    CLIMATE_DIVS_HEATING = "ClimateDivisions.Heating.txt"
    PRIOR_YEAR = (
        str((datetime.datetime.now() - datetime.timedelta(weeks=52)).year) + "/"
    )

    def __init__(
        self,
        states: list | str,
        base_year: int = 0,
        climate_divisions: bool = False,
        mode: Mode = None,
    ) -> None:
        if isinstance(states, str):
            states = [e.upper() for e in states.split(",")]

        assert self.valid_states_input(states)
        if base_year:
            base_year = abs(base_year)
            assert self.valid_year_input(base_year)
        self.states_selected = states
        self.base_year = base_year
        self.climate_divs = climate_divisions
        self.current_year = datetime.datetime.now().year
        self.length = 0
        self._raw = True
        self._normals = False
        self._differences = False
        self._cumulative = False
        self.mode = mode
        if base_year:
            self.prior_year = base_year - 1
        else:
            self.prior_year = self.current_year - 1

    @staticmethod
    def valid_states_input(states: list[str]) -> bool:
        if any(map(lambda e: len(e) != 2, states)):
            raise InvalidState(
                "'states' query parameter expects a comma-seperated "
                "list of 2-character state identifiers "
                "(i.e. 'FL' for 'Florida')"
            )
        return True

    @staticmethod
    def valid_year_input(input_year: int) -> bool:
        current_year = datetime.datetime.now().year
        if len(str(input_year)) != 4:
            raise InvalidYear(
                "Base year should be a 4 digit number representing a year (i.e. 2023)",
            )
        elif input_year > current_year:
            raise InvalidYear(
                f"Cannot pull data for a year beyond the current year: {current_year}",
            )

        return True

    async def get_customer_climate_codes(self) -> list:
        customers = pd.read_csv("./data/ga_customers.csv").set_index("ID")
        customer_name = customers.loc[self.customer].at["Customer"]
        self.customer_name = customer_name
        branches = pd.read_csv(
            "./data/ga_branches.csv", dtype={"Climate Division": int}
        )
        return list(
            set(
                branches.loc[
                    branches["company_id"] == self.customer, "Climate Division"
                ].to_list()
            )
        )

    def metadata(self) -> dict:
        if self.base_year:
            base_year = self.base_year
        else:
            base_year = self.current_year
        result = {"length": self.length, "base_year": base_year}
        response_data = []
        if self.customer:
            result |= {"customer": self.customer_name}
        if self._raw:
            return result | {"response_data": "raw"}
        if self._normals:
            response_data.append("normals")
        if self._cumulative:
            response_data.append("cumulative")
        if self._differences:
            response_data.append("differences")
            result |= {"comparison_year": self.prior_year}

        return result | {"response_data": ", ".join(response_data)}

    def full_url_base_daily(self) -> str:
        if self.base_year:
            result = self.BASE_URL + str(self.base_year) + "/"
        else:
            result = self.BASE_URL + self.LATEST

        result += self.mode_and_divs_or_states()
        return result

    def mode_and_divs_or_states(self) -> str:
        match self.mode, self.climate_divs:
            case "heating", True:
                return self.CLIMATE_DIVS_HEATING
            case "heating", False:
                return self.STATES_HEATING
            case "cooling", True:
                return self.CLIMATE_DIVS_COOLING
            case "cooling", False:
                return self.STATES_COOLING
            case _:
                raise Exception()

    def full_url_comparison_year(self) -> str:
        result = self.BASE_URL + str(self.prior_year) + "/"
        result += self.mode_and_divs_or_states()
        return result

    def full_url_base_normals(self) -> str:
        result = self.BASE_URL + self.NORMALS
        result += self.mode_and_divs_or_states()
        return result

    async def get_current_daily(self) -> pd.DataFrame:
        data = pd.read_csv(self.full_url_base_daily(), skiprows=3, delimiter="|")
        data = data.set_index("Region")
        first_observation_year = int(data.columns.to_list()[0][:4])

        if first_observation_year == self.prior_year:
            # edge case for latest data pulling the year prior
            # at the beginning of the new year
            self.prior_year -= 1

        data.columns = [pd.to_datetime(date, format=r"%Y%m%d") for date in data.columns]
        if self.climate_divs:
            data = await self.match_climate_ids_to_states(data)
        data = data.T
        # Source Data may have nonsense negative values like -9999
        # for every state. Filter those out.
        data = data[data.ge(0).all(1)]
        return data

    async def get_prior_year_daily(self) -> pd.DataFrame:
        data = pd.read_csv(self.full_url_comparison_year(), skiprows=3, delimiter="|")
        data = data.set_index("Region")
        first_observation_year = int(data.columns.to_list()[0][:4])

        if calendar.isleap(first_observation_year):
            data = data.loc[:, ~data.columns.str.endswith("0229")]

        data.columns = [pd.to_datetime(date, format=r"%Y%m%d") for date in data.columns]
        if self.climate_divs:
            data = await self.match_climate_ids_to_states(data)
        data = data.T
        data = data.loc[:, (self.states_selected)]
        data = data.reset_index()
        data["ref_date_index"] = data["index"] + pd.DateOffset(years=1)
        data = data.set_index("ref_date_index").drop(
            columns="index", level=0 if self.climate_divs else None
        )
        return data

    async def get_normals_daily(self) -> pd.DataFrame:
        data = pd.read_csv(self.full_url_base_normals(), skiprows=3, delimiter="|")
        data = data.set_index("Region")
        ref_year = self.base_year if self.base_year else self.current_year

        if not calendar.isleap(ref_year):
            data = data.loc[:, ~data.columns.str.endswith("0229")]

        data.columns = [
            pd.to_datetime(str(ref_year) + date, format=r"%Y%m%d")
            for date in data.columns
        ]
        if self.climate_divs:
            data = await self.match_climate_ids_to_states(data)
        data = data.T
        data = data.loc[:, (self.states_selected)]
        self._normals = True
        return data

    async def degree_days_diff_yoy(self) -> dict:
        current_year_obs = await self.get_current_daily()
        prior_year_obs = await self.get_prior_year_daily()
        cum_diffs_df = cumulative_differences(current_year_obs, prior_year_obs)
        # BUG: Totals, if I keep them, should apply by date,
        # summing the average of the climate divisions
        if not self.climate_divs:
            cum_diffs_df["total"] = cum_diffs_df.apply(sum, axis=1)
        self._cumulative = True
        self._differences = True
        self._raw = False
        return self.formatted_output(cum_diffs_df)

    async def degree_days_cumulative(self, normals: bool):
        if normals:
            observations = await self.get_normals_daily()
        else:
            observations = await self.get_current_daily()
        self._cumulative = True
        self._raw = False
        return self.formatted_output(observations.cumsum())

    async def degree_days(self) -> dict:
        df = await self.get_current_daily()
        return self.formatted_output(df)

    async def get_climate_div_county_state_map(self) -> pd.DataFrame:
        return pd.read_csv("./data/region_id_mapping.csv")

    async def match_climate_ids_to_states(self, data: pd.DataFrame) -> pd.DataFrame:
        data = data.reset_index()
        reference: pd.DataFrame = await self.get_climate_div_county_state_map()
        data = data.merge(reference, left_on="Region", right_on="Region ID")
        # formatting the region column so it shows the region name with the region ID in parentheses
        data["Region"] = data["Name"].str.cat(
            data["Region"].astype(str).str[-2:].apply(lambda x: f"({x})"), sep=" "
        )
        data = data.drop(columns=["CD", "Name", "Region ID"]).set_index(
            ["ST", "Region"]
        )
        return data

    def formatted_output(self, dataframe: pd.DataFrame) -> dict:
        self.length = len(dataframe)
        return {"metadata": self.metadata()} | df_to_list_objs_w_date_indx_as_attr(
            dataframe, "observations"
        )
