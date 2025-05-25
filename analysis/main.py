import os, re, json, hashlib, uuid
from typing import Optional
from fastapi import FastAPI, HTTPException
import asyncpg, httpx

DB_DSN = os.getenv("DB_DSN")
FILESTORE_URL = os.getenv("FILESTORE_URL")
WORD_CLOUD_ENDPOINT = os.getenv("WORD_CLOUD_ENDPOINT")

app = FastAPI(title="File Analysis Service", version="1.0.0")

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS analysis (
    id            UUID PRIMARY KEY,
    paragraphs    INT,
    words         INT,
    chars         INT,
    sha256        TEXT,
    duplicate_of  UUID   REFERENCES analysis(id),
    cloud_url     TEXT
);
"""

@app.on_event("startup")
async def startup():
    app.state.pool = await asyncpg.create_pool(DB_DSN)
    async with app.state.pool.acquire() as c:
        await c.execute(CREATE_SQL)

async def _load_file(fid: str) -> bytes:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{FILESTORE_URL}/files/{fid}")
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, "file storage unavailable")
    return resp.content

def _checksum(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def _basic_stats(text: str):
    paragraphs = len([p for p in text.splitlines() if p.strip()])
    words = len(re.findall(r"\b\w+\b", text, flags=re.UNICODE))
    return paragraphs, words, len(text)

async def _build_wordcloud(text: str) -> Optional[str]:
    if not WORD_CLOUD_ENDPOINT:
        return None
    tokens = re.findall(r"\w{4,}", text.lower())
    if not tokens:
        return None
    top = " ".join(tokens[:100])
    payload = {"format": "png", "width": 500, "height": 300, "text": top}
    async with httpx.AsyncClient() as client:
        resp = await client.post(WORD_CLOUD_ENDPOINT, data=json.dumps(payload))
        if resp.status_code in (200, 201):
            return str(resp.url)
    return None

@app.get("/analysis/{fid}")
async def analyse(fid: str):
    async with app.state.pool.acquire() as c:
        cached = await c.fetchrow("SELECT id, paragraphs, words, chars FROM analysis WHERE id=$1::uuid", fid)
        if cached:
            return {
                "id": str(cached["id"]),
                "paragraphs": cached["paragraphs"],
                "words": cached["words"],
                "chars": cached["chars"],
            }

    data = await _load_file(fid)
    sha = _checksum(data)
    text = data.decode("utf-8", errors="ignore")
    paragraphs, words, chars = _basic_stats(text)

    async with app.state.pool.acquire() as c:
        dup = await c.fetchrow("SELECT id FROM analysis WHERE sha256=$1 LIMIT 1", sha)
        dup_id = dup["id"] if dup else None

    cloud_url = await _build_wordcloud(text)

    async with app.state.pool.acquire() as c:
        await c.execute(
            """
        INSERT INTO analysis(id,paragraphs,words,chars,sha256,duplicate_of,cloud_url)
        VALUES($1,$2,$3,$4,$5,$6,$7)
        """,
            uuid.UUID(fid),
            paragraphs,
            words,
            chars,
            sha,
            dup_id,
            cloud_url,
        )

    return {
        "id": fid,
        "paragraphs": paragraphs,
        "words": words,
        "chars": chars,
    }
