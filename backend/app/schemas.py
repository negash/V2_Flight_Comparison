"""Schemas for flight search requests and responses."""
from typing import List
from pydantic import BaseModel
# from pydantic.networks import HttpUrl


class Flight(BaseModel):
    """Flight details."""
    # id: str
    airline: str
    price: float
    departure: str
    arrival: str
    duration: str
    # search_link: Optional[HttpUrl] = None


class FlightSearchRequest(BaseModel):
    """Flight search request parameters."""
    query: str


class FlightSearchResponse(BaseModel):
    """Flight search response containing a list of flights."""
    flights: List[Flight]
