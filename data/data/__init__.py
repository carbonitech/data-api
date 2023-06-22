import pandas as pd
import datetime

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