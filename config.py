"""
Configuration and environment variables for Animal Transport Agent.
"""
import os
from dataclasses import dataclass
import httpx


# API Keys
YANDEX_API_KEY = os.getenv("YANDEX_MAPS_API_KEY", "")
ORS_API_KEY = os.getenv("ORS_API_KEY", "")

# Flags
YANDEX_MOCK = os.getenv("YANDEX_MAPS_MOCK", "false").lower() == "true"

# LLM Configuration
QWEN_MODEL_NAME = os.getenv("QWEN_MODEL_NAME", "Qwen/Qwen2.5-7B-Instruct")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "http://127.0.0.1:8000/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "EMPTY")

# Captioning
CAPTION_MODEL_ID = "microsoft/Florence-2-base"


@dataclass
class AppDeps:
    """Shared dependencies injected into agent tools."""
    http_client: httpx.AsyncClient
    yandex_api_key: str = YANDEX_API_KEY
    yandex_mock: bool = YANDEX_MOCK
    ors_api_key: str = ORS_API_KEY
