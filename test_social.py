import asyncio
import os
import sys

from zoya.services.zoya_social import twitter_write_tweet
from livekit.agents import RunContext

async def main():
    print("Testing functionality directly...")
    try:
        # Mocking empty context since tools don't heavily use Livekit RunContext structure
        class MockContext:
            pass
            
        result = await twitter_write_tweet(MockContext(), topic="AI agents future", tone="engaging")
        print("\nTEST RESULT:\n", result)
    except Exception as e:
        print("\nTEST FAILED:\n", e)

if __name__ == "__main__":
    asyncio.run(main())
