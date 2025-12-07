"""
Open-Meteo weather forecasting service.
"""
from datetime import datetime
from pydantic_ai import RunContext
from config import AppDeps
from models import WeatherSnapshot


async def get_weather_forecast(
    ctx: RunContext[AppDeps],
    lat: float,
    lon: float,
    hours_ahead: int = 0,
) -> WeatherSnapshot:
    """
    Get weather forecast from Open-Meteo.
    
    Args:
        ctx: Pydantic AI context
        lat: Latitude in decimal degrees
        lon: Longitude in decimal degrees
        hours_ahead: Hours into future (0 = current)
        
    Returns:
        WeatherSnapshot with temperature, precipitation, wind
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,precipitation,wind_speed_10m",
        "forecast_hours": max(hours_ahead + 1, 1),
        "timezone": "auto",
    }

    resp = await ctx.deps.http_client.get(
        "https://api.open-meteo.com/v1/forecast", 
        params=params, 
        timeout=10.0
    )
    resp.raise_for_status()
    data = resp.json()

    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    precs = hourly.get("precipitation", [])
    winds = hourly.get("wind_speed_10m", [])

    if not times:
        raise ValueError("Open-Meteo: no hourly data returned")

    idx = min(hours_ahead, len(times) - 1)

    ts_str = times[idx]
    ts = datetime.fromisoformat(ts_str)

    temp = float(temps[idx]) if idx < len(temps) else 0.0
    prec = float(precs[idx]) if idx < len(precs) else 0.0
    wind = float(winds[idx]) if idx < len(winds) else 0.0

    is_heavy_prec = prec >= 2.0
    is_strong_wind = wind >= 10.0

    summary_parts = [
        f"{temp:.1f}°C",
        f"{prec:.1f} mm/h precipitation",
        f"{wind:.1f} m/s wind",
    ]
    if is_heavy_prec:
        summary_parts.append("heavy precipitation")
    if is_strong_wind:
        summary_parts.append("strong wind")

    return WeatherSnapshot(
        latitude=lat,
        longitude=lon,
        time=ts,
        temperature_c=temp,
        precipitation_mm=prec,
        wind_speed_mps=wind,
        is_heavy_precipitation=is_heavy_prec,
        is_strong_wind=is_strong_wind,
        summary=", ".join(summary_parts),
    )
