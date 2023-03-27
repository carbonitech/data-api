from os import getenv
from fastapi import FastAPI, Request, Response
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from routes import *

app = FastAPI()

app.include_router(fred)
app.include_router(cdd)
app.include_router(customers)

db_url = getenv('DATABASE_URL').replace("postgres://","postgresql://")
engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# middleware for recording all API calls
@app.middleware('http')
async def record_api_call(request: Request, call_next):
    db = next(get_db())
    response = Response("Internal server error", status_code=500)  
    try:
        user_agent = request.headers.get("user-agent")
        parameters = str(request.query_params)
        host, port = request.client
        path = request.url.path

        db.execute(
                text("INSERT INTO data_api_request_log (agent, path, parameters, ip) VALUES (:a, :b, :c, :d);"),
                params={"a": user_agent, "b": path, "c": parameters, "d": host+':'+str(port)}
            )
        db.commit()
        response = await call_next(request)
    except Exception as e:
        import traceback
        traceback.print_exc(e)

    return response