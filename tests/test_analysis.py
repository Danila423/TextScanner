import httpx, pytest, time, uuid

BASE = "http://localhost:8000"


@pytest.mark.asyncio
async def test_not_found():
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{BASE}/reports/{uuid.uuid4()}")
        assert r.status_code == 404 or r.status_code == 500
