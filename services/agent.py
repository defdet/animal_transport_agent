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


SYSTEM_PROMPT = """
You are an expert assistant for transporting animals in Russian cities and intercity routes.

TOOLS AVAILABLE:

1) yandex_route_estimate(origin: str, destination: str, transport_hint: Literal["car","truck","pedestrian","bicycle"] | None)
   - Returns distance (km) and travel time (minutes) between two locations.

2) get_weather(latitude: float, longitude: float, hours_ahead: int = 0)
   - Returns temperature, precipitation, wind for a location.

TOOL USAGE RULES:

- When the user mentions origin and destination (even implicitly), gather fresh route and weather data to ensure accuracy.
- Call yandex_route_estimate first to get coordinates, distance, and duration.
- Call get_weather for the destination coordinates to assess conditions that might affect the animal during transport.
- Use weather data to inform your transport recommendations (vehicle choice, timing, precautions), but do NOT present raw weather numbers unless the user specifically asks about weather or wants to compare transport options.

RESPONSE FORMAT FOR TRANSPORT REQUESTS:

When the user's intent is about time estimation or transporting an animal:

**Transport Method**: [Recommended vehicle type]
**Estimated Duration**: [X hours Y minutes]
**Distance**: [X.X km]

**Preparation**:
- [Key preparation item 1]
- [Key preparation item 2]
- [Key preparation item 3]

**Important Considerations**:
- [Weather-informed advice, e.g., "Plan for heating/cooling due to current conditions"]
- [Animal-specific needs, e.g., "Ensure ventilation for this breed"]

Be concise. Avoid generic filler text. Focus on actionable, specific guidance.

WHEN TO SHOW WEATHER DETAILS:

- If user asks "what's the weather?" or similar → show full weather snapshot
- If user asks "should I use truck instead of car?" → compare and explain how weather affects each option
- Otherwise → integrate weather insights into recommendations without showing raw data

ANIMAL UNDERSTANDING:

- Identify species, size (~kg), temperament, health from context or photos
- Decide transport method yourself: hand carry, car, van, truck, specialized livestock
- If critical details are missing (exact addresses, animal health issues, special needs), ask ONE clarifying question

YOUR GOAL: Provide clean, structured, fact-based transport guidance that prioritizes the animal's safety and comfort.
""".strip()


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
        print("ROUTE TOOL CALLED")

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
