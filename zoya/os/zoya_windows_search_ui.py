import asyncio
from zoya.os.keyboard_mouse_CTRL import controller, with_temporary_activation
from livekit.agents import function_tool

@function_tool
async def ui_windows_search_open(app_name: str) -> str:
    """
    Search and open any application or file using the Windows Search UI (taskbar search).
    Use this when user says "window k sath search bar mein search karo" or "search bar se open karo".

    Args:
        app_name: The name of the app or file to search for.
    """
    try:
        # Step 1: Open Windows Search UI
        # We use Win+S to be specific
        await with_temporary_activation(controller.press_hotkey, ["win", "s"])
        await asyncio.sleep(1.0) # Wait for UI to appear

        # Step 2: Type the search term
        await with_temporary_activation(controller.type_text, app_name)
        await asyncio.sleep(1.5) # Wait for results to populate

        # Step 3: Press Enter to open the first/best match
        await with_temporary_activation(controller.press_key, "enter")
        
        return f"✅ Windows Search UI mein '{app_name}' search kiya aur enter dabaya."
    except Exception as e:
        return f"❌ Windows Search UI tool fail ho gaya: {e}"
