import httpx, pytest

BASE = "http://localhost:8000"

@pytest.mark.asyncio
async def test_happy_flow(tmp_path):
    p = tmp_path / "a.txt"
    p.write_text("hello\n\nworld")
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{BASE}/reports", files={"file": ("a.txt", p.read_bytes())})
        assert r.status_code == 201
        rid = r.json()["id"]

        # анализ
        a = await c.get(f"{BASE}/reports/{rid}")
        assert a.status_code == 200
        body = a.json()
        assert body["words"] == 2
        assert body["paragraphs"] == 2
