"""V2 Flight Comparison API using FastAPI and LangChain Agent."""
from fastapi import FastAPI
from app.schemas import FlightSearchRequest, FlightSearchResponse
from app.flight_service import search_flights_from_query


app = FastAPI(title="V2 Flight Comparison API (Function Calling)")


@app.post("/search", response_model=FlightSearchResponse)
async def search_flights(req: FlightSearchRequest):
    flights = await search_flights_from_query(req.query)
    return {"flights": flights}
