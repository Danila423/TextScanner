import os, httpx
from fastapi import FastAPI, UploadFile, File, HTTPException, Response

FILESTORE = os.getenv("FILESTORE_URL")
ANALYSIS = os.getenv("ANALYSIS_URL")

app = FastAPI(
    title="API Gateway",
    version="1.0.0",
    description="Маршрутизация запросов между микросервисами",
)



@app.post("/reports", status_code=201)
async def upload_report(file: UploadFile = File(...)):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{FILESTORE}/files", files={"file": (file.filename, await file.read())}
        )
    if resp.status_code != 201:
        raise HTTPException(resp.status_code, resp.text)
    return resp.json()  # {"id": ...}



@app.get("/reports/{rid}")
async def get_analysis(rid: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{ANALYSIS}/analysis/{rid}")
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, resp.text)
    return resp.json()



@app.get("/files/{rid}", response_class=Response, responses={404: {"model": None}})
async def get_file(rid: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{FILESTORE}/files/{rid}")
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, resp.text)
    return Response(content=resp.content, media_type="text/plain")
