import httpx, pytest, uuid

BASE = "http://localhost:8000"


@pytest.mark.asyncio
async def test_duplicate(tmp_path):
    p = tmp_path / "same.txt"
    p.write_text("dup")
    async with httpx.AsyncClient() as c:
        r1 = await c.post(f"{BASE}/reports", files={"file": p.open("rb")})
        r2 = await c.post(f"{BASE}/reports", files={"file": p.open("rb")})
        assert r1.json()["id"] == r2.json()["id"]
