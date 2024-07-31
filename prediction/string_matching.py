from io import BytesIO
import json
import joblib
import numpy as np
import pandas as pd
from fastapi import APIRouter, Request
from sklearn.ensemble import RandomForestClassifier
from prediction import s3

string_matching = APIRouter(prefix="/string_matching")
MODEL_PREDICTION_THRESHOLD = 0.5


def get_RFMODEL() -> RandomForestClassifier:
    s3_key = "CLASSIFICATION_MODEL/rf_model_n_1000_2024_07_26.joblib"
    _, model_bytes = s3.get_file(s3_key)
    model_file = BytesIO(model_bytes)
    return joblib.load(model_file)


RF_MODEL = get_RFMODEL()


@string_matching.post("/cmmssns")
async def cmmssns(request: Request):
    json_data = await request.json()
    model_features = list(RF_MODEL.feature_names_in_)
    df = pd.read_json(json.dumps(json_data), orient="spilt")
    # predict
    predictions = RF_MODEL.predict_proba(X=df.loc[:, model_features])[:, 1]
    df["predictions"] = np.where(
        predictions >= MODEL_PREDICTION_THRESHOLD, predictions, 0
    )
    max_score = df["predictions"].max()
    if max_score == 0:
        result = 0
    else:
        cb_id: int = df.loc[df["predictions"] == max_score, "branch_id"].item()
        result = cb_id
    return {"result": result}


@string_matching.get("/cmmssns/model-features")
def cmmssns_model_features():
    features = list(RF_MODEL.feature_names_in_)
    return {"data": features}
