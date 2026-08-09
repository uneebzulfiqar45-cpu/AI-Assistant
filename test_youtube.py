import asyncio
import urllib.parse

async def test_youtube():
    query = "arijit singh songs"
    encoded = urllib.parse.quote(query)
    url = f"https://www.youtube.com/results?search_query={encoded}"
    print("Opening URL:", url)
    proc = await asyncio.create_subprocess_shell(f'start "" "{url}"')
    await asyncio.sleep(3)
    print("Done!")

asyncio.run(test_youtube())
