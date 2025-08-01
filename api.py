from dotenv import load_dotenv

load_dotenv()
from os import getenv
from datetime import datetime, UTC
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, Depends
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import text
from sqlalchemy.orm import Session

from data.routes import fred, cdd
from testing.mspa import mspa
from api_access_gate import access_gate, access_keys
from db import get_db
from logging import getLogger

logger = getLogger("uvicorn.info")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting lifespan")
    # setup access keys
    global access_keys
    db: Session = next(get_db())
    try:
        logger.info("Setting up access keys")
        sql = """
            SELECT id, keyhash, expires, revoked
            FROM data_api_access_keys
            WHERE NOT revoked
            AND (expires IS NULL OR expires > :now)
        """
        response = (
            db.execute(text(sql), params=dict(now=datetime.now(UTC)))
            .mappings()
            .fetchall()
        )
        if response:
            access_keys.setup_keystore(records=response)
    except Exception as e:
        logger.error(e)
    finally:
        db.close()
    yield
    # teardown logic would go here


app = FastAPI(title="Carboni Tech API", version="0.3.1", lifespan=lifespan)
app.include_router(fred, dependencies=[Depends(access_gate)])
app.include_router(cdd, dependencies=[Depends(access_gate)])
app.include_router(mspa, dependencies=[Depends(access_gate)])

ORIGINS = getenv("ORIGINS")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# middleware for recording all API calls
@app.middleware("http")
async def record_api_call(request: Request, call_next):
    db: Session = next(get_db())
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
    except Exception as e:
        import traceback

        traceback.print_exc(e)
    finally:
        return await call_next(request)
