"""
Routes for Cooling Degree Days
"""

import datetime
from fastapi import APIRouter, HTTPException
from data.climate_prediction_center import ClimatePredictionCenter

cdd = APIRouter(prefix="/cdd", tags=["Cooling Degree Days"])

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

## COOLING DEGREE DAYS (CDD) ##
@cdd.get("")
async def get_cooling_degree_days_raw(
        states: str,
        base_year: int|None = None,
        climate_divisions: bool=False
    ):
    states_split = [e.upper() for e in states.split(",")]
    assert valid_states_input(states_split)
    if base_year:
        if base_year < 0:
            base_year = abs(base_year)
        assert valid_year_input(base_year)

    cpc = ClimatePredictionCenter(states_split, base_year, climate_divisions)
    return await cpc.cooling_degree_days()


@cdd.get("/cumulative")
async def get_cumulative_cdd(
        states: str,
        normals: bool=False,
        base_year: int|None=None,
        climate_divisions: bool=False
    ):
    states_split = [e.upper() for e in states.split(",")]
    assert valid_states_input(states_split)
    if base_year:
        if base_year < 0:
            base_year = abs(base_year)
        assert valid_year_input(base_year)
    cpc = ClimatePredictionCenter(states_split, base_year, climate_divisions)
    return await cpc.cooling_degree_days_cumulative(normals)


@cdd.get("/cumulative-differences")
async def get_cooling_degree_day_cumulative_differences_yoy(
        states: str,
        base_year: int|None=None,
        climate_divisions: bool=False
    ):
    states_split = [e.upper() for e in states.split(",")]
    assert valid_states_input(states_split)

    if base_year:
        if base_year < 0:
            base_year = abs(base_year)
        assert valid_year_input(base_year)

    cpc = ClimatePredictionCenter(states_split, base_year, climate_divisions)
    return await cpc.cooling_degree_days_diff_yoy()
