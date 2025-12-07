"""
Animal Transport Assistant CLI with multi-turn conversation support.
"""
import asyncio
import os
from typing import Optional

import httpx
from config import AppDeps
from agent import create_agent
from services import caption_image, initialize_captioning_model


async def run_one_turn(
    agent,
    deps: AppDeps,
    user_text: str,
    image_path: Optional[str],
    message_history: list,
) -> tuple[str, list]:
    """
    Execute single conversation turn with optional image.
    
    Returns:
        Tuple of (response_text, updated_message_history)
    """
    full_text = user_text

    if image_path:
        image_path = image_path.strip()
        if os.path.exists(image_path) and os.path.isfile(image_path):
            caption = caption_image(image_path)
            full_text = (
                f"{user_text}\n\n[Additional context from user photo: {caption}]"
            )
        else:
            print(f"[info] Image not found, ignoring: {image_path}")

    result = await agent.run(full_text, deps=deps, message_history=message_history)
    return result.output, result.all_messages()


async def main() -> None:
    """Multi-turn conversation CLI for animal transport assistance."""
    # Initialize captioning model at startup
    initialize_captioning_model()
    
    # Create agent
    agent = create_agent()

    async with httpx.AsyncClient() as client:
        deps = AppDeps(http_client=client)

        print("🐾 Animal Transport Assistant (Pydantic AI + Qwen2.5-7B)")
        print("Multi-turn conversation enabled. Empty text → exit.\n")

        message_history = []

        while True:
            user_text = input("Text (empty to quit): ").strip()
            if not user_text:
                break

            image_path = input("Image path (optional, Enter for none): ").strip()
            if not image_path:
                image_path = None

            try:
                response_text, message_history = await run_one_turn(
                    agent, deps, user_text, image_path, message_history
                )
                print("\nAssistant:\n", response_text, "\n")
            except Exception as e:
                print(f"\n[Error] {e}\n")


if __name__ == "__main__":
    asyncio.run(main())
