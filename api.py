from dotenv import load_dotenv

load_dotenv()
from os import getenv
from datetime import datetime, UTC
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from data.routes import *
from ai.app.main import app as ai
from testing.mspa import mspa

app = FastAPI(title="Carboni Tech API", version="0.3.0")

app.include_router(fred)
app.include_router(cdd)
app.include_router(customers)
app.include_router(ai)
app.include_router(mspa)

ORIGINS = getenv("ORIGINS")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db_url = getenv("DATABASE_URL").replace("postgres://", "postgresql://")
engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# middleware for recording all API calls
@app.middleware("http")
async def record_api_call(request: Request, call_next):
    db = next(get_db())
    sql = """
        INSERT INTO data_api_request_log (agent, path, parameters, ip, time) 
        VALUES (:a, :b, :c, :d, :e);
    """
    response = Response("Internal server error", status_code=500)
    try:
        time = datetime.now(UTC)
        user_agent = request.headers.get("user-agent")
        parameters = str(request.query_params)
        host, port = request.client
        path = request.url.path

        db.execute(
            text(sql),
            params={
                "a": user_agent,
                "b": path,
                "c": parameters,
                "d": host + ":" + str(port),
                "e": time,
            },
        )
        db.commit()
        response = await call_next(request)
    except Exception as e:
        import traceback

        traceback.print_exc(e)
    return response
