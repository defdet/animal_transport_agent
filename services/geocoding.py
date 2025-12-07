"""
Yandex Geocoder service for address to coordinates conversion.
"""
from pydantic_ai import RunContext
from config import AppDeps


async def geocode_address(
    ctx: RunContext[AppDeps], address: str
) -> tuple[float, float]:
    """
    Convert human-readable address to (lat, lon) using Yandex Geocoder.
    
    Returns:
        Tuple of (latitude, longitude) in decimal degrees
    """
    if not ctx.deps.yandex_api_key:
        raise RuntimeError("YANDEX_MAPS_API_KEY is not set")

    params = {
        "apikey": ctx.deps.yandex_api_key,
        "geocode": address,
        "format": "json",
        "lang": "ru_RU",
        "results": 1,
    }

    resp = await ctx.deps.http_client.get(
        "https://geocode-maps.yandex.ru/1.x", 
        params=params, 
        timeout=10.0
    )
    resp.raise_for_status()
    data = resp.json()

    members = (
        data.get("response", {})
        .get("GeoObjectCollection", {})
        .get("featureMember", [])
    )
    if not members:
        raise ValueError(f"Yandex Geocoder: no result for '{address}'")

    point = (
        members[0]
        .get("GeoObject", {})
        .get("Point", {})
        .get("pos", "")
    )
    if not point:
        raise ValueError(f"Yandex Geocoder: no coordinates for '{address}'")

    # Yandex returns "lon lat"
    lon_str, lat_str = point.split()
    return float(lat_str), float(lon_str)
