"""
Routes for Cooling Degree Days
"""

from fastapi import APIRouter
from data.data.climate_prediction_center import init_cpc

dd = APIRouter(prefix="/degree-days")
cdd = APIRouter(prefix="/cooling", tags=["Cooling Degree Days"])
hdd = APIRouter(prefix="/heating", tags=["Heating Degree Days"])

dd.include_router(cdd)
dd.include_router(hdd)


## COOLING DEGREE DAYS (CDD) ##
@cdd.get("")
async def get_cooling_degree_days_raw(
    states: str | None = None,
    base_year: int | None = None,
    climate_divisions: bool = False,
):
    mode = "cooling"
    cpc = init_cpc(states, base_year, climate_divisions, mode)
    return await cpc.degree_days()


@cdd.get("/cumulative")
async def get_cumulative_cdd(
    states: str | None = None,
    normals: bool = False,
    base_year: int | None = None,
    climate_divisions: bool = False,
):
    mode = "cooling"
    cpc = init_cpc(states, base_year, climate_divisions, mode)
    return await cpc.degree_days_cumulative(normals)


@cdd.get("/cumulative-differences")
async def get_cooling_degree_day_cumulative_differences_yoy(
    states: str | None = None,
    base_year: int | None = None,
    climate_divisions: bool = False,
):
    mode = "cooling"
    cpc = init_cpc(states, base_year, climate_divisions, mode)
    return await cpc.degree_days_diff_yoy()


## HEATING DEGREE DAYS (HDD) ##
@hdd.get("")
async def get_heating_degree_days_raw(
    states: str | None = None,
    base_year: int | None = None,
    climate_divisions: bool = False,
):
    mode = "heating"
    cpc = init_cpc(states, base_year, climate_divisions, mode)
    return await cpc.degree_days()


@hdd.get("/cumulative")
async def get_cumulative_hdd(
    states: str | None = None,
    normals: bool = False,
    base_year: int | None = None,
    climate_divisions: bool = False,
):
    mode = "heating"
    cpc = init_cpc(states, base_year, climate_divisions, mode)
    return await cpc.degree_days_cumulative(normals)


@hdd.get("/cumulative-differences")
async def get_heating_degree_day_cumulative_differences_yoy(
    states: str | None = None,
    base_year: int | None = None,
    climate_divisions: bool = False,
):
    mode = "heating"
    cpc = init_cpc(states, base_year, climate_divisions, mode)
    return await cpc.degree_days_diff_yoy()
