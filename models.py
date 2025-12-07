"""
Data models for transport routing and weather.
"""
from datetime import datetime
from pydantic import BaseModel, Field


class RouteEstimate(BaseModel):
    """Route estimation result from routing service."""
    origin_query: str
    destination_query: str
    origin_lat: float
    origin_lon: float
    destination_lat: float
    destination_lon: float
    distance_km: float
    duration_minutes: int
    raw_mode: str = Field(
        "driving",
        description="Routing mode used (driving/truck/walking/cycling).",
    )


class WeatherSnapshot(BaseModel):
    """Weather data snapshot from Open-Meteo."""
    latitude: float
    longitude: float
    time: datetime
    temperature_c: float
    precipitation_mm: float
    wind_speed_mps: float
    is_heavy_precipitation: bool
    is_strong_wind: bool
    summary: str
