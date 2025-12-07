"""
OpenRouteService routing for distance and duration estimates.
"""
from typing import Literal
from pydantic_ai import RunContext
from config import AppDeps
from models import RouteEstimate
from .geocoding import geocode_address


async def get_route_estimate(
    ctx: RunContext[AppDeps],
    origin: str,
    destination: str,
    profile: Literal[
        "driving-car",
        "driving-hgv",
        "foot-walking",
        "cycling-regular",
    ] = "driving-car",
) -> RouteEstimate:
    """
    Get route distance and duration via OpenRouteService.
    
    Args:
        ctx: Pydantic AI context with dependencies
        origin: Starting address/location
        destination: Destination address/location
        profile: Routing profile (vehicle type)
        
    Returns:
        RouteEstimate with distance, duration, and coordinates
    """
    # Mock mode for testing
    if ctx.deps.yandex_mock:
        return RouteEstimate(
            origin_query=origin,
            destination_query=destination,
            origin_lat=55.7558,
            origin_lon=37.6176,
            destination_lat=59.9311,
            destination_lon=30.3609,
            distance_km=706.0,
            duration_minutes=480,
            raw_mode=profile,
        )

    if not ctx.deps.ors_api_key:
        raise RuntimeError("ORS_API_KEY is not set")

    # Geocode addresses
    lat1, lon1 = await geocode_address(ctx, origin)
    lat2, lon2 = await geocode_address(ctx, destination)

    # Call OpenRouteService Directions API
    url = f"https://api.openrouteservice.org/v2/directions/{profile}"
    
    headers = {
        "Authorization": ctx.deps.ors_api_key,
        "Content-Type": "application/json",
    }
    
    body = {
        "coordinates": [
            [lon1, lat1],  # ORS expects [lon, lat]
            [lon2, lat2],
        ]
    }

    resp = await ctx.deps.http_client.post(
        url,
        headers=headers,
        json=body,
        timeout=10.0
    )
    resp.raise_for_status()
    data = resp.json()

    summary = data['routes'][0]['summary']
    duration_s = summary['duration']
    distance_m = summary['distance']

    if not summary:
        raise ValueError(f"ORS: no route for '{origin}' → '{destination}'")

    distance_km = distance_m / 1000.0 if distance_m else 0.0
    duration_minutes = int(round(duration_s / 60.0)) if duration_s else 0

    print(f"Distance: {distance_km} km")
    
    return RouteEstimate(
        origin_query=origin,
        destination_query=destination,
        origin_lat=lat1,
        origin_lon=lon1,
        destination_lat=lat2,
        destination_lon=lon2,
        distance_km=round(distance_km, 2),
        duration_minutes=duration_minutes,
        raw_mode=profile,
    )
