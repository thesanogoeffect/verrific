import os
import pytest
import requests
from time import sleep

@pytest.fixture(scope="session")
def grobid_url():
    """Get Grobid URL from environment or use default."""
    return os.getenv("GROBID_URL", "http://localhost:8070")

@pytest.fixture(scope="session", autouse=True)
def ensure_grobid_ready(grobid_url):
    """Ensure Grobid service is ready before running tests."""
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get(f"{grobid_url}/api/isalive", timeout=5)
            if response.status_code == 200:
                return
        except requests.exceptions.RequestException:
            pass
        
        if i < max_retries - 1:
            sleep(2)
    
    pytest.fail(f"Grobid service at {grobid_url} is not ready after {max_retries * 2} seconds")