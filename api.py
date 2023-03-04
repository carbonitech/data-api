from fastapi import FastAPI
from routes import fred, cdd

app = FastAPI()

app.include_router(fred.fred)
app.include_router(cdd.cdd)