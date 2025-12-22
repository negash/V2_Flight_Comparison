"""Amadeus API client for flight search."""
import httpx
from app.settings import settings

# API base URL for Amadeus sandbox environment for flight search
AMADEUS_BASE_URL = "https://test.api.amadeus.com"


async def get_access_token():
    """Get Amadeus API access token."""
    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{AMADEUS_BASE_URL}/v1/security/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": settings.AMADEUS_API_KEY,
                "client_secret": settings.AMADEUS_API_SECRET,
            },
        )
        res.raise_for_status()
        return res.json()["access_token"]
