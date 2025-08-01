# data-api
Enriches JSON data series with calculated trend data

## **FRED (Saint Louis Federal Reserve)**  
1. **Request any FRED data series by Series ID from FRED and get *additional* trendline datapoints (observation "value" is provided by FRED)**
    * Rolling 12 Month Total
    * Rolling 12/12 %
    * Rolling 3 Month Total
    * Rolling 3/12 %
  
   **/fred-data**   
        - `series_id`  
        - `fred_api_key`  

2. **Request Housing Inventory given a state  and get *additional* trendline datapoints with trend metrics**
    * Rolling 12 Month Total
    * Rolling 12/12 %
    * Rolling 3 Month Total
    * Rolling 3/12 %
  
    **/fred-data/housing-inventory**  
        - `state` : two letter state identifier (i.e. GA for 'Georgia')  
        - `fred_api_key`  

### **Example 1**  

Normal observation output from FRED (in JSON) for series code **GANA**, all non-farm employment in the state of Georgia. (Metadata and other observations excluded for brevity.)

        {
            "realtime_start": "2023-02-17",
            "realtime_end": "2023-02-17",
            "date": "2022-11-01",
            "value": "4834.1"
        }

Output of data-api
> Request: GET https://api.carbonitech.com/fred-data?series_id=GANA

        {
            "date": "2022-11-01",
            "realtime_start": "2023-02-17",
            "realtime_end": "2023-02-17",
            "value": "4834.1",
            "rolling_12_month_total": "57329.1",
            "rolling_12_12_pct": "0.04922638242733268",
            "rolling_3_month_total": "14501.7",
            "rolling_3_12_pct": "0.04407646063573201"
        }


### **Example 2**  

Housing Inventory given a state, derived from the latest active and pending listing count
> Request: GET https://api.carbonitech.com/fred-data/housing-inventory?state=GA

      [
        ...,
        {
          "date": "2023-01-01",
          "realtime_start": "2023-03-12",
          "realtime_end": "2023-03-12",
          "value": "37622.0",
          "rolling_12_month_total": "516865.0",
          "rolling_12_12_pct": "-0.03260975354116136",
          "rolling_3_month_total": "123695.0",
          "rolling_3_12_pct": "-0.0154180463576159"
        },
        {
          "date": "2023-02-01",
          "realtime_start": "2023-03-12",
          "realtime_end": "2023-03-12",
          "value": "39217.0",
          "rolling_12_month_total": "517308.0",
          "rolling_12_12_pct": "-0.02492040962887987",
          "rolling_3_month_total": "118126.0",
          "rolling_3_12_pct": "-0.010429668847542484"
        }
      ]
___
## **Climate Prediction Center - Cooling Degree Days**
Request Cooling Degree Days either in raw numbers, cumulative, or the cumulative difference compared to the prior year, for States and [Climate Divisions](https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/regional_monitoring/CLIM_DIVS/states_counties_climate-divisions.shtml)
- /cdd  
        - `states`: a single 2-letter state identifier or a list of states (required if customer_id not provided)  
        - `base_year`: the year you'd like to query. Defaults to the current year  
        - `climate_divisions`: The default is state-level data. Setting this to True will break out data by state climate divisions  
        - `customer_id`: Specific HVAC Wholesalers can be used to query for climate regions that correspond to their branch footprint. A list of supported customers can be found [here](https://api.carbonitech.com/customers)
- /cdd/cumulative  
        - `states`: a single 2-letter state identifier or a list of states (required if customer_id not provided)  
        - `base_year`: the year you'd like to query. Defaults to the current year  
        - `climate_divisions`: The default is state-level data. Setting this to True will break out data by state climate divisions  
        - `customer_id`: Specific HVAC Wholesalers can be used to query for climate regions that correspond to their branch footprint. A list of supported customers can be found [here](https://api.carbonitech.com/customers)  
- /cdd/cumulative-differences  
        - `states`: a single 2-letter state identifier or a list of states (required if customer_id not provided)  
        - `normals`: Returns the normal accumulated degree days as estimated by the CPC. The data is invariant to the year, but providing `base_year` will change the dates displayed in the data.  
        - `base_year`: the year you'd like to query. Defaults to the current year  
        - `climate_divisions`: The default is state-level data. Setting this to True will break out data by state climate divisions  
        - `customer_id`: Specific HVAC Wholesalers can be used to query for climate regions that correspond to their branch footprint. A list of supported customers can be found [here](https://api.carbonitech.com/customers)  

### **Example**

Querying for cumulative degree days in 2020 for Florida, Alabama, and California, broken out by Climate Divisions

> Request: GET https://api.carbonitech.com/cdd/cumulative?states=FL,AL,CA&base_year=2020&climate_divisions=true

        {
          "metadata": {
            "length": 366,
            "base_year": 2020,
            "response_data": "cumulative"
          },
          "observations": [
            {
              "date": "2020-01-01",
              "FL": {
                "NORTHWEST (01)": 0,
                "NORTH (02)": 0,
                "NORTH CENTRAL (03)": 0,
                "SOUTH CENTRAL (04)": 0,
                "EVERGLADES (05)": 0,
                "LOWER EAST COAST (06)": 0,
                "KEYS (07)": 0
              },
              "AL": {
                "NORTHERN VALLEY (01)": 0,
                "APPALACHIAN MOUNTAIN (02)": 0,
                "UPPER PLAINS (03)": 0,
                "EASTERN VALLEY (04)": 0,
                "PIEDMONT PLATEAU (05)": 0,
                "PRAIRIE (06)": 0,
                "COASTAL PLAIN (07)": 0,
                "GULF (08)": 0
              },
              "CA": {
                "NORTH COAST DRAINAGE (01)": 0,
                "SACRAMENTO DRNG. (02)": 0,
                "NORTHEAST INTER. BASINS (03)": 0,
                "CENTRAL COAST DRNG. (04)": 0,
                "SAN JOAQUIN DRNG. (05)": 0,
                "SOUTH COAST DRNG. (06)": 0,
                "SOUTHEAST DESERT BASIN (07)": 0
              }
            }, ...