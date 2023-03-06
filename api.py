from fastapi import FastAPI
from routes import *

app = FastAPI()

app.include_router(fred)
app.include_router(cdd)
app.include_router(customers)