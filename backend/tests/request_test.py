"""This script demonstrates how to use the search API to find flights."""
import json
import requests


def search_flights():
    """Search for flights using the search API."""
    response = requests.post(
        "http://localhost:8000/search",
        json={"query": "Find cheap flights from San Francisco to Paris next Friday"},
        timeout=20
    )
    response.raise_for_status()
    return response.json()


# print(search_flights())
print(json.dumps(search_flights(), indent=2))

# once local server start running (uvicorn app.main:app --reload)
# run this script from main directory (python tests/request_test.py)
