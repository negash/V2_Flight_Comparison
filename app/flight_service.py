
"""Flight service module. Handles flight search functionality."""
from datetime import date, timedelta
import json
import httpx
from fastapi import HTTPException
from app.amadeus_client import get_access_token
# from app.llm_parser import parse_flight_query
from app.llm_parser import parse_flight_query


AMADEUS_SEARCH_URL = "https://test.api.amadeus.com/v2/shopping/flight-offers"


async def search_flights_from_query(query: str) -> list[dict]:
    """Search for flights based on a natural language query."""
    parsed = await parse_flight_query(query)

    if isinstance(parsed, str):
        parsed = json.loads(parsed)

    required_keys = {"origin", "destination", "date"}
    if not all(k in parsed for k in required_keys):
        raise HTTPException(400, f"Invalid parse result: {parsed}")

    try:
        flight_date = date.fromisoformat(parsed["date"])
    except ValueError as exc:
        raise HTTPException(400, "Invalid departure date") from exc

    if flight_date <= date.today():
        flight_date = date.today() + timedelta(days=7)

    token = await get_access_token()

    timeout = httpx.Timeout(
        connect=10.0,
        read=30.0,
        write=10.0,
        pool=10.0,
    )

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            res = await client.get(
                AMADEUS_SEARCH_URL,
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "originLocationCode": parsed["origin"],
                    "destinationLocationCode": parsed["destination"],
                    "departureDate": flight_date.isoformat(),
                    "adults": 1,
                    "currencyCode": "USD",
                    "max": 3,
                },
            )
    except httpx.ReadTimeout as exc:
        raise HTTPException(
            status_code=504,
            detail="Flight search provider timed out"
        ) from exc
    if res.status_code != 200:
        raise HTTPException(res.status_code, res.text)

    data = res.json().get("data", [])

    flights = [
        {
            # "id": offer["id"],  # "air": offer["
            "airline": offer["validatingAirlineCodes"][0],
            "price": float(offer["price"]["total"]),
            "departure": offer["itineraries"][0]["segments"][0]["departure"]["iataCode"],
            "arrival": offer["itineraries"][0]["segments"][-1]["arrival"]["iataCode"],
            "duration": offer["itineraries"][0]["duration"],
            # "booking_reference": offer["id"]  # "air["offer["id
        }
        for offer in data[:5]
    ]

    return sorted(flights, key=lambda f: f["price"])
