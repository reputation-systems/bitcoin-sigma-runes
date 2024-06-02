import pytest
import httpx

BASE_URL = "http://127.0.0.1:8000"

sample = {
    "sigma_script": "sigma-script-test",
    "tokens": [{"id": "token-1", "amount": 100}],
    "r4": "r4-reg",
    "r5": "r5-reg",
    "r6": "r6-reg",
    "r7": "r7-reg",
    "r8": "r8-reg",
    "r9": "r9-reg"
}

@pytest.fixture(scope="module")
def http_client():
    with httpx.Client(base_url=BASE_URL) as client:
        yield client

def test_create_reputation_test(http_client):
    response = http_client.post("/add/", json=sample)
    assert response.status_code == 201

if __name__ == "__main__":
    pytest.main(["-v", __file__])
