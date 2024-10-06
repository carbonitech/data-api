from fastapi import APIRouter, Request, UploadFile

mspa = APIRouter(prefix="/mspa")


@mspa.get("")
def get_req(r: Request):
    for header, value in r.headers.items():
        print(f"\t{header}: {value}")


@mspa.post("")
def post_req(r: Request, file: UploadFile = None):
    print("--------- HEADERS ---------")
    for header, value in r.headers.items():
        print(f"\t{header}: {value}")
    print("--------- BODY ---------")
    print(r.body())
