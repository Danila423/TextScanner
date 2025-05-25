import pytest, subprocess, time, httpx, os, shutil

@pytest.fixture(scope="session", autouse=True)
def compose():
    proc = subprocess.Popen(["docker", "compose", "up", "--build", "-d"])
    proc.wait()
    time.sleep(10)
    yield
    subprocess.run(["docker", "compose", "down", "-v"])
