# data-api
Enriches JSON data series with calculated trend data

## **FRED (Saint Louis Federal Reserve)**  
Request any FRED data series by Series ID from FRED and get *additional* trendline datapoints (observation "value" is provided by FRED)
1. Rolling 12 Month Total
2. Rolling 12/12 %
3. Rolling 3 Month Total
4. Rolling 3/12 %  

### **Example**  

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
