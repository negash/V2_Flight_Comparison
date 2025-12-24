# """Flight service module. Handles flight search functionality."""
from datetime import date, timedelta
import json
import httpx
from fastapi import HTTPException
import opik
from opik import opik_context

from app.amadeus_client import get_access_token
from app.llm_parser import parse_flight_query

AMADEUS_SEARCH_URL = "https://test.api.amadeus.com/v2/shopping/flight-offers"


async def search_flights_from_query(query: str) -> list[dict]:
    """Search for flights based on a natural language query."""
    span = opik_context.get_current_span_data()
    if span:
        opik_context.update_current_span(
            tags=["service:flight-search", "provider:amadeus"],
            metadata={"request_received": 1}
        )
    # Opik records the start_time when the block begins and end_time when it finishes
    with opik.start_as_current_span(name="llm_parsing_phase", type="llm"):
        parsed = await parse_flight_query(query)
        if isinstance(parsed, str):
            parsed = json.loads(parsed)

    try:

        # parse LLM query to get origin, destination, and date
        parsed = await parse_flight_query(query)
        if isinstance(parsed, str):
            parsed = json.loads(parsed)

        required_keys = {"origin", "destination", "date"}
        if not all(k in parsed for k in required_keys):
            raise ValueError(f"Missing keys in LLM response: {parsed}")

        # validate and adjust date
        try:
            flight_date = date.fromisoformat(parsed["date"])
            if flight_date <= date.today():
                flight_date = date.today() + timedelta(days=7)
        except (ValueError, KeyError) as exc:
            raise ValueError(
                f"Invalid or missing date in LLM response: {parsed.get('date')}"
            ) from exc

        # API Call with detailed Error Handling
        token = await get_access_token()
        timeout = httpx.Timeout(10.0, read=30.0)

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
            # Handle HTTP Errors
            res.raise_for_status()

        # Process Results
        data = res.json().get("data", [])
        flights = [
            {
                "airline": offer["validatingAirlineCodes"][0],
                "price": float(offer["price"]["total"]),
                "departure": offer["itineraries"][0]["segments"][0]["departure"]["iataCode"],
                "arrival": offer["itineraries"][0]["segments"][-1]["arrival"]["iataCode"],
                "duration": offer["itineraries"][0]["duration"],
            }
            for offer in data[:5]
        ]
        flights = sorted(flights, key=lambda f: f["price"])

        # Logging and Metadata Update
        if span:
            opik_context.update_current_span(
                metadata={"results_count": len(flights), "parse_success": 1}
            )

        return flights

    except Exception as e:
        # Log Error and Update Span Metadata
        if span:
            opik_context.update_current_span(
                metadata={"parse_success": 0},

                error_info={"exception_type": type(
                    e).__name__, "message": str(e)}
            )

        # Handle Specific Exceptions for HTTP Responses
        if isinstance(e, httpx.HTTPStatusError):
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Amadeus API Error: {e.response.text}"
            ) from e

        elif isinstance(e, (httpx.RequestError, httpx.TimeoutException)):
            raise HTTPException(
                status_code=504,
                detail="Flight search provider timed out or unreachable"
            ) from e

        elif isinstance(e, ValueError):
            raise HTTPException(
                status_code=400,
                detail=str(e)
            ) from e

        raise HTTPException(
            status_code=500,
            detail="Internal Server Error"
        ) from e
