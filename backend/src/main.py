# <ai_context>
# This file is the main entry point for the Polymarket AI agent system.
# It coordinates the event loop, environment configuration, and
# starts up WebSocket polling and the AI agent's logic.
# </ai_context>

import asyncio
import os
from dotenv import load_dotenv
from polymarket_client import PolymarketClient
from polytrader_agent import PolymarketAIAgent

async def main():
    load_dotenv()  # Load environment variables (API keys, secrets, etc.)

    # Instantiate Polymarket client for WebSocket + REST
    pm_client = PolymarketClient(
        api_key=os.environ.get("POLYMARKET_API_KEY", ""),
        api_secret=os.environ.get("POLYMARKET_API_SECRET", ""),
        private_key=os.environ.get("POLYMARKET_WALLET_PRIVKEY", ""),
    )

    # Instantiate AI Agent
    ai_agent = PolymarketAIAgent(polymarket_client=pm_client)

    # Start Polymarket connection (WebSocket + scheduled tasks)
    await pm_client.start_streams(ai_agent.handle_event)

    # Example periodic tasks or analysis
    # Could use something like a background scheduler or tasks
    # For demonstration, just keep running until manually stopped
    while True:
        await asyncio.sleep(3600)  # Sleep 1 hour as a placeholder

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down AI agent...") 