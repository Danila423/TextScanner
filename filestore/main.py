import os, uuid, hashlib, aiofiles, asyncpg
from fastapi import FastAPI, UploadFile, File, HTTPException, Response

DB_DSN = os.getenv("DB_DSN")
STORAGE_PATH = os.getenv("STORAGE_PATH", "/store")
os.makedirs(STORAGE_PATH, exist_ok=True)

app = FastAPI(title="File Storing Service", version="1.0.0")

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS files(
    id UUID PRIMARY KEY,
    filename TEXT,
    sha256 TEXT UNIQUE,
    location TEXT
);
"""

@app.on_event("startup")
async def startup():
    app.state.pool = await asyncpg.create_pool(DB_DSN)
    async with app.state.pool.acquire() as c:
        await c.execute(CREATE_SQL)

def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

@app.post("/files", status_code=201)
async def save_file(file: UploadFile = File(...)):
    data = await file.read()
    sha = _sha(data)
    async with app.state.pool.acquire() as c:
        row = await c.fetchrow("SELECT id FROM files WHERE sha256=$1", sha)
        if row:
            return {"id": str(row["id"])}
        fid = uuid.uuid4()
        location = f"{STORAGE_PATH}/{fid}.txt"
        async with aiofiles.open(location, "wb") as fp:
            await fp.write(data)
        await c.execute(
            "INSERT INTO files(id,filename,sha256,location) VALUES($1,$2,$3,$4)",
            fid, file.filename, sha, location
        )
    return {"id": str(fid)}


@app.get("/files/{fid}", response_class=Response)
async def download_file(fid: str):
    async with app.state.pool.acquire() as c:
        row = await c.fetchrow("SELECT location FROM files WHERE id=$1::uuid", fid)
    if not row:
        raise HTTPException(404, "file not found")
    async with aiofiles.open(row["location"], "rb") as fp:
        data = await fp.read()
    return Response(content=data, media_type="text/plain")
