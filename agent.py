"""
Pydantic AI agent with routing and weather tools.
"""
from typing import Optional, Literal
from pydantic_ai import Agent, RunContext, ModelSettings
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from config import AppDeps, QWEN_MODEL_NAME, OPENAI_BASE_URL, OPENAI_API_KEY
from models import RouteEstimate, WeatherSnapshot
from services import get_route_estimate, get_weather_forecast
from prompts import SYSTEM_PROMPT


def create_agent() -> Agent[AppDeps]:
    """Create Pydantic AI agent with routing and weather tools."""
    provider = OpenAIProvider(
        base_url=OPENAI_BASE_URL,
        api_key=OPENAI_API_KEY,
    )

    settings = ModelSettings(temperature=0.6)

    model = OpenAIChatModel(
        QWEN_MODEL_NAME,
        provider=provider,
        settings=settings,
    )

    agent = Agent(
        model=model,
        deps_type=AppDeps,
        system_prompt=SYSTEM_PROMPT,
    )

    # Tool 1: Route estimation
    @agent.tool
    async def yandex_route_estimate(
        ctx: RunContext[AppDeps],
        origin: str,
        destination: str,
        transport_hint: Optional[Literal["car", "truck", "pedestrian", "bicycle"]] = None,
    ) -> RouteEstimate:
        """
        Estimate route distance and travel time between two locations.
        
        Uses Yandex Geocoder for addresses and OpenRouteService for routing.
        """
        print("ROUTE TOOL CALLED") # Some models (e.x. Qwen 2.5 VL) like to simulate tool calling. Wanna make sure tool is actually called

        profile_map = {
            "car": "driving-car",
            "truck": "driving-hgv",
            "pedestrian": "foot-walking",
            "bicycle": "cycling-regular",
        }
        profile = profile_map.get(transport_hint or "car", "driving-car")
        return await get_route_estimate(ctx, origin, destination, profile=profile)

    # Tool 2: Weather forecast
    @agent.tool
    async def get_weather(
        ctx: RunContext[AppDeps],
        latitude: float,
        longitude: float,
        hours_ahead: int = 0,
    ) -> WeatherSnapshot:
        """Get weather forecast for animal transport safety assessment."""
        print("WEATHER TOOL CALLED")
        return await get_weather_forecast(ctx, latitude, longitude, hours_ahead)

    return agent
