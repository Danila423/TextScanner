import pytest, subprocess, time, httpx, os, shutil

@pytest.fixture(scope="session", autouse=True)
def compose():
    # запускаем docker-compose только один раз для всего тестового сета
    proc = subprocess.Popen(["docker", "compose", "up", "--build", "-d"])
    proc.wait()
    # подождать пока сервисы поднялись
    time.sleep(10)
    yield
    subprocess.run(["docker", "compose", "down", "-v"])
