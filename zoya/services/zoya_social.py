import os
import re
import base64
import httpx
import asyncio
import pyautogui
import mss
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import function_tool, RunContext

# Import existing low-level tools
from zoya.os.keyboard_mouse_CTRL import (
    click_at_position_tool, type_text_tool, press_key_tool, press_hotkey_tool
)
from zoya.os.Jarvis_window_CTRL import open_app, focus_window

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(dotenv_path=BASE_DIR / ".env")

# === API Keys ===
CLAUDE_SONNET_KEY = os.getenv("OPENROUTER_API_KEY_Claude_Sonnet")
CLAUDE_SONNET_TOOLS_KEY = os.getenv("OPENROUTER_API_KEY_Claude_Sonnet_Tools")
GEMINI_PRO_KEY = os.getenv("OPENROUTER_API_KEY_Gemini_Pro")
GPT4O_KEY = os.getenv("OPENROUTER_API_KEY_OpenAI_GPT4o")
GPT35_KEY = os.getenv("OPENROUTER_API_KEY_GPT35")  # Corrected key name

# Priority order: gpt-4o-mini (Working) > Claude Sonnet > Gemini Pro > GPT4o
VISION_KEYS = [
    (GPT35_KEY, "openai/gpt-4o-mini"),
    (CLAUDE_SONNET_KEY, "anthropic/claude-3.5-sonnet"),
    (CLAUDE_SONNET_TOOLS_KEY, "anthropic/claude-3.5-sonnet"),
    (GEMINI_PRO_KEY, "google/gemini-pro-1.5"),
    (GPT4O_KEY, "openai/gpt-4o"),
]

# ==========================================
# Core Helper: Take Screenshot + Ask Vision
# ==========================================

def _take_screenshot(path: Path):
    """Take a screenshot and save it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with mss.mss() as sct:
        sct.shot(output=str(path))

async def _ask_vision_for_coords(base64_img: str, prompt: str) -> str:
    """Ask Vision AI for coordinates. Returns 'x, y' string or None."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    full_prompt = f"""You are an expert UI automation assistant. 
Represent the current screenshot as a coordinate system where (0,0) is TOP-LEFT and (1000,1000) is BOTTOM-RIGHT.
{prompt}
CRITICAL: Return ONLY two numbers in this format: [x, y]
Example: [500, 500]
Do not include any conversational text or explanation."""

    for key, model_id in VISION_KEYS:
        if not key:
            continue
        headers = {
            "Authorization": f"Bearer {key.strip('\"')}",
            "Content-Type": "application/json",
            "HTTP-Referer": "zoya-agent",
            "X-Title": "Zoya WhatsApp Vision"
        }
        payload = {
            "model": model_id,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": full_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}
                    ]
                }
            ]
        }
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    return resp.json()['choices'][0]['message']['content'].strip()
        except Exception:
            continue
    return None

def _parse_coords(coords_text: str):
    """Parse '[x, y]' normalized string to actual physical pixels using Regex."""
    try:
        # 1. Debug Log: Save raw response
        log_file = DATA_DIR / "vision_debug.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now()}: {coords_text}\n")

        # 2. Use Regex to find ALL numbers in the response
        # This handles "[500, 400]", "500,400", "The point is at (500, 400)" etc.
        numbers = re.findall(r'\d+', coords_text)
        
        if len(numbers) >= 2:
            norm_x = float(numbers[0])
            norm_y = float(numbers[1])
            
            # Ensure numbers are between 0 and 1000
            if norm_x > 1000: norm_x = 1000
            if norm_y > 1000: norm_y = 1000

            # 3. Convert 0-1000 to actual Screen Size
            width, height = pyautogui.size()
            real_x = int((norm_x / 1000.0) * width)
            real_y = int((norm_y / 1000.0) * height)
            
            return real_x, real_y
        
        print(f"DEBUG: No valid numbers found in: {coords_text}")
        return None, None
    except Exception as e:
        print(f"DEBUG: Parse Error: {e} | Raw: {coords_text}")
        return None, None

async def _screenshot_to_b64(path: Path) -> str:
    """Read image file and return base64 string."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')


# ==========================================
# TOOL 1: YouTube Search (UI)
# ==========================================

@function_tool
async def youtube_search_ui(context: RunContext, query: str = "") -> str:
    """
    Search for a video on YouTube OR open the main page if query is empty.
    This is the most reliable method — works whether YouTube is open or not.
    """
    import urllib.parse
    import urllib.request
    import re
    try:
        if not query or query.strip() == "":
            search_url = "https://www.youtube.com/"
            status = "✅ YouTube ka main page open kar diya!"
        else:
            encoded_query = urllib.parse.quote(query)
            search_url = f"https://www.youtube.com/results?search_query={encoded_query}"
            status = f"✅ YouTube pe '{query}' search kar diya! Browser mein results open ho rahe hain."
            
            # Autoplay mechanism: try to scrape the first video ID from the search results
            try:
                req = urllib.request.Request(search_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
                html = urllib.request.urlopen(req, timeout=5).read().decode('utf-8', errors='ignore')
                video_ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
                if video_ids:
                    # Filter out any non-standard video IDs or shorts if necessary, but first is usually best
                    search_url = f"https://www.youtube.com/watch?v={video_ids[0]}"
                    status = f"✅ YouTube pe '{query}' search kar ke pehla result autoplay kar diya!"
            except Exception as e:
                pass # Fallback to just the search page if extraction fails

        # Directly open URL via Windows 'start' command — always works
        await asyncio.create_subprocess_shell(f'start "" "{search_url}"')
        
        return status
    except Exception as e:
        return f"❌ YouTube open/search mein error aaya: {e}"

@function_tool
async def youtube_play_result(context: RunContext, index: int = 1) -> str:
    """
    Play a specific video from the search results after a search has been performed.
    Uses AI Vision to find and click the correct video based on the index (1 for first, 2 for second etc).
    """
    screenshot_path = BASE_DIR / "data" / f"yt_play_{index}.jpg"
    
    # 1. Wait for page to load (increased to 8s for ads/slow connections)
    await asyncio.sleep(8)
    _take_screenshot(screenshot_path)
    b64 = await _screenshot_to_b64(screenshot_path)
    
    # 2. Ask Vision to find coordinates (Enhanced prompt for ad avoidance)
    prompt = (
        f"Find the center coordinates (x, y) of the {index}-th organic video result (thumbnail or title) on this YouTube page. "
        "CRITICAL: Ignore 'Ad', 'Sponsored', or 'Promoted'. "
        "Also, if there is a 'Play' button overlay on the thumbnail, target its center. "
        "If multiple thumbnails exist, pick the first one which is NOT a banner. "
        "Output format: [x, y]"
    )
    
    coords_text = await _ask_vision_for_coords(b64, prompt)
    
    if not coords_text:
        # Fallback 1: Just press Enter if we can't find coords
        await press_key_tool('enter')
        return f"⚠️ Coordinates nahi milin, 'Enter' daba kar play karne ki koshish ki."

    x, y = _parse_coords(coords_text)
    if x is None:
        await press_key_tool('enter')
        return f"⚠️ Coordinates parse nahi hue, 'Enter' daba kar play karne ki koshish ki."

    # 3. Use the new robust mouseDown/Up click
    await click_at_position_tool(x, y)
    await asyncio.sleep(1)
    
    # 4. Final Fallback: Press 'k' or 'Enter' to ensure playback starts
    await press_key_tool('k')
    await asyncio.sleep(0.5)
    await press_key_tool('enter')
    
    if screenshot_path.exists():
        screenshot_path.unlink()

    return f"✅ YouTube pe video number {index} play karne ki koshish ki gayi hai! Enjoy."


# ==========================================
# TOOL 2: Instagram Search (UI)
# ==========================================

@function_tool
async def instagram_search_ui(context: RunContext, query: str = "") -> str:
    """
    Search for a profile on Instagram OR open the main page if query is empty.
    """
    import urllib.parse

    focused = await focus_window("instagram")
    
    if not query or query.strip() == "":
        search_url = "https://www.instagram.com/"
        status = "Instagram ka main page open kar diya."
        if not focused:
            return await open_app("instagram")
        return status
    else:
        encoded_query = urllib.parse.quote(query)
        search_url = f"https://www.instagram.com/explore/search/keyword/?q={encoded_query}"
        status = f"Instagram pe '{query}' search kar diya."

    if not focused:
        # Browser isn't even for Instagram, just open the full search URL directly!
        return await open_app(search_url)

    # If already focused on an existing Instagram tab, use address bar to search there
    await press_key_tool("escape")
    await asyncio.sleep(0.3)
    await press_hotkey_tool(["ctrl", "l"])
    await asyncio.sleep(0.5)
    await type_text_tool(search_url)
    await asyncio.sleep(0.3)
    await press_key_tool("enter")
    await asyncio.sleep(2)

    return status


# ==========================================
# TOOL 3: Facebook Search (UI)
# ==========================================

@function_tool
async def facebook_search_ui(context: RunContext, query: str = "") -> str:
    """
    Search on Facebook OR open the main page if query is empty.
    """
    import urllib.parse

    focused = await focus_window("facebook")
    
    if not query or query.strip() == "":
        search_url = "https://www.facebook.com/"
        status = "Facebook ka main page open kar diya."
        if not focused:
            return await open_app("facebook")
        return status
    else:
        encoded_query = urllib.parse.quote(query)
        search_url = f"https://www.facebook.com/search/top?q={encoded_query}"
        status = f"Facebook pe '{query}' search kar diya."

    if not focused:
        # Just open the full search URL directly!
        return await open_app(search_url)

    # Already focused, search in current tab
    await press_key_tool("escape")
    await asyncio.sleep(0.3)
    await press_hotkey_tool(["ctrl", "l"])
    await asyncio.sleep(0.5)
    await type_text_tool(search_url)
    await asyncio.sleep(0.3)
    await press_key_tool("enter")
    await asyncio.sleep(2)

    return status


# ==========================================
# TOOL 4: Twitter/X Search (UI)
# ==========================================

@function_tool
async def twitter_search_ui(context: RunContext, query: str = "") -> str:
    """
    Search on Twitter/X OR open the main page if query is empty.
    """
    import urllib.parse

    focused = await focus_window("x") or await focus_window("twitter")
    
    if not query or query.strip() == "":
        search_url = "https://x.com/home"
        status = "X (Twitter) ka main page open kar diya."
        if not focused:
            return await open_app("twitter")
        return status
    else:
        encoded_query = urllib.parse.quote(query)
        search_url = f"https://x.com/search?q={encoded_query}&src=typed_query"
        status = f"X pe '{query}' search kar diya."

    if not focused:
        return await open_app(search_url)

    # Already focused, search in current tab
    await press_key_tool("escape")
    await asyncio.sleep(0.3)
    await press_hotkey_tool(["ctrl", "l"])
    await asyncio.sleep(0.5)
    await type_text_tool(search_url)
    await asyncio.sleep(0.3)
    await press_key_tool("enter")
    await asyncio.sleep(2)

    return status


# ==========================================
# TOOL 5: LinkedIn Search (UI)
# ==========================================

@function_tool
async def linkedin_search_ui(context: RunContext, query: str = "") -> str:
    """
    Search on LinkedIn OR open the main page if query is empty.
    """
    import urllib.parse

    focused = await focus_window("linkedin")
    
    if not query or query.strip() == "":
        search_url = "https://www.linkedin.com/feed/"
        status = "LinkedIn ka main page open kar diya."
        if not focused:
            return await open_app("linkedin")
        return status
    else:
        encoded_query = urllib.parse.quote(query)
        search_url = f"https://www.linkedin.com/search/results/all/?keywords={encoded_query}"
        status = f"LinkedIn pe '{query}' search kar diya."

    if not focused:
        return await open_app(search_url)

    # Already focused, search in current tab
    await press_key_tool("escape")
    await asyncio.sleep(0.3)
    await press_hotkey_tool(["ctrl", "l"])
    await asyncio.sleep(0.5)
    await type_text_tool(search_url)
    await asyncio.sleep(0.3)
    await press_key_tool("enter")
    await asyncio.sleep(2)

    return status


# ==========================================
# TOOL 2: WhatsApp - Contact Search & Open Chat
# ==========================================

@function_tool
async def whatsapp_open_chat(context: RunContext, contact_name: str) -> str:
    """
    Open WhatsApp and search for a contact or group, then open their chat.

    Args:
        contact_name: Name of the contact or group to open.
    """
    await open_app("whatsapp")
    await asyncio.sleep(7)

    screenshot_path = BASE_DIR / "data" / "wa_capture.jpg"
    _take_screenshot(screenshot_path)
    b64 = await _screenshot_to_b64(screenshot_path)

    coords_text = await _ask_vision_for_coords(
        b64,
        "Find the center coordinates of the WhatsApp search bar (the search icon or 'Search or start new chat' input box)."
    )

    if not coords_text:
        return "❌ WhatsApp search bar nahi mili."

    x, y = _parse_coords(coords_text)
    if x is None:
        return f"❌ Coordinates parse nahi hue: {coords_text}"

    # Click search bar and type contact name
    await click_at_position_tool(x, y)
    await asyncio.sleep(0.5)
    await type_text_tool(contact_name)
    await asyncio.sleep(2)

    # Now take another screenshot to find the first result
    _take_screenshot(screenshot_path)
    b64 = await _screenshot_to_b64(screenshot_path)

    result_coords_text = await _ask_vision_for_coords(
        b64,
        f"Find the center coordinates of the first search result matching '{contact_name}' in the chat list."
    )

    if not result_coords_text:
        return f"✅ WhatsApp mein '{contact_name}' search kiya. Lekin result nahi mila — manually select karein."

    rx, ry = _parse_coords(result_coords_text)
    if rx is None:
        return f"❌ Result coordinates galat: {result_coords_text}"

    await click_at_position_tool(rx, ry)

    if screenshot_path.exists():
        screenshot_path.unlink()

    return f"✅ '{contact_name}' ki chat WhatsApp pe khol di gayi hai."


# ==========================================
# TOOL 3: WhatsApp - Send Message
# ==========================================

@function_tool
async def whatsapp_send_message(context: RunContext, contact_name: str, message: str) -> str:
    """
    Send a WhatsApp message to a contact. First opens the chat, then types and sends the message.

    Args:
        contact_name: Name of the contact or group.
        message: The message to send.
    """
    # Step 1: Open the chat first
    open_result = await whatsapp_open_chat(context, contact_name)
    if "❌" in open_result:
        return open_result

    await asyncio.sleep(1.5)

    # Step 2: Find the message input box
    screenshot_path = BASE_DIR / "data" / "wa_msg_capture.jpg"
    _take_screenshot(screenshot_path)
    b64 = await _screenshot_to_b64(screenshot_path)

    coords_text = await _ask_vision_for_coords(
        b64,
        "Find the center coordinates of the WhatsApp message text input box at the bottom of the chat."
    )

    if not coords_text:
        return "❌ Message box nahi mila."

    x, y = _parse_coords(coords_text)
    if x is None:
        return f"❌ Message box coordinates galat: {coords_text}"

    # Step 3: Click, type, send
    await click_at_position_tool(x, y)
    await asyncio.sleep(0.5)
    await type_text_tool(message)
    await asyncio.sleep(0.3)
    await press_key_tool("enter")

    if screenshot_path.exists():
        screenshot_path.unlink()

    return f"✅ '{contact_name}' ko message bhej diya: \"{message}\""


# ==========================================
# TOOL 4: WhatsApp - Answer Incoming Call
# ==========================================

@function_tool
async def whatsapp_accept_call(context: RunContext) -> str:
    """
    Accept an incoming WhatsApp call. Uses AI Vision to find and click the green accept button.
    """
    screenshot_path = BASE_DIR / "data" / "wa_call_capture.jpg"
    _take_screenshot(screenshot_path)
    b64 = await _screenshot_to_b64(screenshot_path)

    coords_text = await _ask_vision_for_coords(
        b64,
        "Find the center coordinates of the GREEN call accept button (phone icon, typically at the bottom of the screen or in a notification popup)."
    )

    if not coords_text:
        return "❌ Call accept button nahi mila. Shayad koi call nahi aa rahi."

    x, y = _parse_coords(coords_text)
    if x is None:
        return f"❌ Coordinates parse nahi hue: {coords_text}"

    await click_at_position_tool(x, y)

    if screenshot_path.exists():
        screenshot_path.unlink()

    return f"✅ WhatsApp call accept kar li gayi! (Button coordinates: {x}, {y})"


# ==========================================
# TOOL 5: WhatsApp - Reject / End Call
# ==========================================

@function_tool
async def whatsapp_reject_call(context: RunContext) -> str:
    """
    Reject an incoming or end an ongoing WhatsApp call. Uses AI Vision to find the red decline/end button.
    """
    screenshot_path = BASE_DIR / "data" / "wa_reject_capture.jpg"
    _take_screenshot(screenshot_path)
    b64 = await _screenshot_to_b64(screenshot_path)

    coords_text = await _ask_vision_for_coords(
        b64,
        "Find the center coordinates of the RED call reject or end-call button (typically a phone icon facing down or a red circle)."
    )

    if not coords_text:
        return "❌ Decline/End button nahi mila."

    x, y = _parse_coords(coords_text)
    if x is None:
        return f"❌ Coordinates parse nahi hue: {coords_text}"

    await click_at_position_tool(x, y)

    if screenshot_path.exists():
        screenshot_path.unlink()

    return f"✅ WhatsApp call decline/end kar diya. (Button: {x}, {y})"


# ==========================================
# HELPER: Generate Text Content via AI
# ==========================================

async def _generate_text_with_ai(system_prompt: str, user_prompt: str) -> str:
    """Use OpenRouter AI to generate text content (posts, messages etc)."""
    url = "https://openrouter.ai/api/v1/chat/completions"

    # Use text-focused keys (GPT-4o-mini working, GPT4o, Claude Sonnet)
    text_keys = [
        (GPT35_KEY, "openai/gpt-4o-mini"),
        (GPT4O_KEY, "openai/gpt-4o"),
        (CLAUDE_SONNET_KEY, "anthropic/claude-3.5-sonnet"),
        (GEMINI_PRO_KEY, "google/gemini-pro-1.5"),
    ]

    for key, model_id in text_keys:
        if not key:
            continue
        headers = {
            "Authorization": f"Bearer {key.strip('\"')}",
            "Content-Type": "application/json",
            "HTTP-Referer": "zoya-agent",
            "X-Title": "Zoya LinkedIn Writer"
        }
        payload = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    return resp.json()['choices'][0]['message']['content'].strip()
        except Exception:
            continue
    return None


# ==========================================
# TOOL 6: LinkedIn - Write & Post
# ==========================================

@function_tool
async def linkedin_write_post(context: RunContext, topic: str, tone: str = "professional") -> str:
    """
    Write a LinkedIn post on a given topic using AI, then open LinkedIn and post it automatically.
    The AI writes a professional, engaging post, then navigates to LinkedIn post box and types it.

    Args:
        topic: The topic or idea for the LinkedIn post.
        tone: Tone of the post — 'professional', 'casual', 'inspirational', or 'story'. Default is 'professional'.
    """

    # === Step 1: Generate post content using OpenRouter AI ===
    system_prompt = (
        "You are a professional LinkedIn content writer. "
        "Write engaging, well-structured LinkedIn posts with relevant emojis, hashtags, and line breaks. "
        "Keep it between 150–250 words. Do NOT add any intro like 'Here is your post:'. "
        "Just write the post content directly."
    )
    user_prompt = f"Write a {tone} LinkedIn post about: {topic}"

    post_content = await _generate_text_with_ai(system_prompt, user_prompt)

    if not post_content:
        return "❌ Post content generate nahi ho saka. OpenRouter keys check karein."

    # === Step 2: Open LinkedIn ===
    await open_app("linkedin")
    await asyncio.sleep(6)

    # === Step 3: Take screenshot to find "Start a post" box ===
    screenshot_path = BASE_DIR / "data" / "li_capture.jpg"
    _take_screenshot(screenshot_path)
    b64 = await _screenshot_to_b64(screenshot_path)

    coords_text = await _ask_vision_for_coords(
        b64,
        "Find the center coordinates of the 'Start a post' input box or button at the top of the LinkedIn feed page."
    )

    if not coords_text:
        return f"✅ Post content ready hai, lekin LinkedIn box nahi mila:\n\n{post_content}"

    x, y = _parse_coords(coords_text)
    if x is None:
        return f"✅ Post content ready (coordinates galat):\n\n{post_content}"

    # === Step 4: Click the post box ===
    await click_at_position_tool(x, y)
    await asyncio.sleep(2)  # Wait for post editor to open

    # === Step 5: Find the actual text editor area inside the post modal ===
    _take_screenshot(screenshot_path)
    b64 = await _screenshot_to_b64(screenshot_path)

    editor_coords_text = await _ask_vision_for_coords(
        b64,
        "The LinkedIn post editor/modal is now open. Find the center coordinates of the text input area where you can type the post content."
    )

    if editor_coords_text:
        ex, ey = _parse_coords(editor_coords_text)
        if ex:
            await click_at_position_tool(ex, ey)
            await asyncio.sleep(0.5)

    # === Step 6: Type the post content ===
    await type_text_tool(post_content)
    await asyncio.sleep(1)

    if screenshot_path.exists():
        screenshot_path.unlink()

    return (
        f"✅ LinkedIn post type kar diya gaya!\n\n"
        f"📋 Post Content:\n{post_content}\n\n"
        f"💡 Tip: 'Post' button pr click karo ya mujhe kaho 'post publish karo'."
    )


# ==========================================
# TOOL 7: LinkedIn - Publish Post (Click Post Button)
# ==========================================

@function_tool
async def linkedin_publish_post(context: RunContext) -> str:
    """
    Click the 'Post' button on LinkedIn to publish the post that is currently typed in the editor.
    Call this after linkedin_write_post has been used.
    """
    screenshot_path = BASE_DIR / "data" / "li_publish_capture.jpg"
    _take_screenshot(screenshot_path)
    b64 = await _screenshot_to_b64(screenshot_path)

    coords_text = await _ask_vision_for_coords(
        b64,
        "Find the center coordinates of the blue 'Post' button in the LinkedIn post editor modal. It is usually at the bottom right of the dialog."
    )

    if not coords_text:
        return "❌ 'Post' button nahi mila. Manually click karein."

    x, y = _parse_coords(coords_text)
    if x is None:
        return f"❌ Button coordinates galat: {coords_text}"

    await click_at_position_tool(x, y)

    if screenshot_path.exists():
        screenshot_path.unlink()

    return "✅ LinkedIn post publish ho gayi! 🎉"


# ============================================================
# UNIVERSAL HELPER: Vision-Based Post Writer for Any Platform
# ============================================================

async def _write_and_type_post(
    platform: str,
    open_keyword: str,
    load_wait: float,
    post_box_prompt: str,
    editor_prompt: str,
    content: str,
    screenshot_prefix: str
) -> str:
    """
    Universal helper: Open platform, find the post input box using Vision, type content.
    """
    await open_app(open_keyword)
    await asyncio.sleep(load_wait)

    # Step 1: Find post box
    ss_path = BASE_DIR / "data" / f"{screenshot_prefix}_step1.jpg"
    _take_screenshot(ss_path)
    b64 = await _screenshot_to_b64(ss_path)

    coords_text = await _ask_vision_for_coords(b64, post_box_prompt)
    if not coords_text:
        return f"✅ {platform} khul gayi, post box nahi mila:\n\n{content}"

    x, y = _parse_coords(coords_text)
    if x is None:
        return f"✅ Content ready, coordinates galat:\n\n{content}"

    await click_at_position_tool(x, y)
    await asyncio.sleep(2)

    # Step 2: Find text editor inside opened dialog/modal
    _take_screenshot(ss_path)
    b64 = await _screenshot_to_b64(ss_path)
    editor_text = await _ask_vision_for_coords(b64, editor_prompt)

    if editor_text:
        ex, ey = _parse_coords(editor_text)
        if ex:
            await click_at_position_tool(ex, ey)
            await asyncio.sleep(0.5)

    # Step 3: Type content
    await type_text_tool(content)
    await asyncio.sleep(1)

    if ss_path.exists():
        ss_path.unlink()

    return f"✅ {platform} pe post type ho gaya!\n\n📋 Content:\n{content}"


async def _click_publish_button(platform: str, button_prompt: str, screenshot_prefix: str) -> str:
    """Universal helper: Find and click the publish/submit button using Vision."""
    ss_path = BASE_DIR / "data" / f"{screenshot_prefix}_publish.jpg"
    _take_screenshot(ss_path)
    b64 = await _screenshot_to_b64(ss_path)

    coords_text = await _ask_vision_for_coords(b64, button_prompt)
    if not coords_text:
        return f"❌ {platform} ka publish button nahi mila. Manually click karein."

    x, y = _parse_coords(coords_text)
    if x is None:
        return f"❌ Button coordinates galat: {coords_text}"

    await click_at_position_tool(x, y)

    if ss_path.exists():
        ss_path.unlink()

    return f"✅ {platform} pe post publish ho gayi! 🎉"


# ============================================================
# TOOL 8: Twitter/X — Write & Type Tweet
# ============================================================

@function_tool
async def twitter_write_tweet(context: RunContext, topic: str, tone: str = "engaging") -> str:
    """
    Write an AI-generated tweet on a topic and type it in the Twitter/X compose box.
    Twitter character limit (280 chars) is respected automatically.

    Args:
        topic: The subject or idea for the tweet.
        tone: Tone of tweet — 'engaging', 'funny', 'informational', 'controversial', 'inspirational'. Default 'engaging'.
    """
    system_prompt = (
        "You are a Twitter/X content expert. Write a tweet that is under 270 characters. "
        "It must be punchy, engaging, and include 2-3 relevant hashtags at the end. "
        "Use emojis sparingly. NO intro text like 'Here is...'. Just the tweet."
    )
    content = await _generate_text_with_ai(system_prompt, f"Write a {tone} tweet about: {topic}")
    if not content:
        return "❌ Tweet generate nahi ho saka."

    # Trim to 280 chars if needed
    if len(content) > 270:
        content = content[:267] + "..."

    result = await _write_and_type_post(
        platform="Twitter/X",
        open_keyword="twitter",
        load_wait=5,
        post_box_prompt=(
            "Find the center coordinates of the 'What is happening?!' tweet compose button "
            "or the text input area at the top center or left of the Twitter/X feed."
        ),
        editor_prompt=(
            "The tweet compose box is now open or highlighted. "
            "Find the center of the active text input area where tweet text can be typed."
        ),
        content=content,
        screenshot_prefix="tw"
    )
    return result


@function_tool
async def twitter_publish_tweet(context: RunContext) -> str:
    """
    Click the 'Post' button on Twitter/X to publish the currently composed tweet.
    Call this after twitter_write_tweet.
    """
    return await _click_publish_button(
        platform="Twitter/X",
        button_prompt=(
            "Find the center coordinates of the blue 'Post' button in the tweet compose area. "
            "It may say 'Post' or 'Tweet' and is typically blue, top-right of the compose box."
        ),
        screenshot_prefix="tw"
    )


# ============================================================
# TOOL 9: Facebook — Write & Post
# ============================================================

@function_tool
async def facebook_write_post(context: RunContext, topic: str, tone: str = "friendly") -> str:
    """
    Write an AI-generated Facebook post and type it into the Facebook compose box.

    Args:
        topic: The subject or idea for the Facebook post.
        tone: Tone — 'friendly', 'informational', 'inspirational', 'promotional', 'story'. Default 'friendly'.
    """
    system_prompt = (
        "You are a Facebook content creator. Write an engaging Facebook post. "
        "Use a warm, conversational tone with emojis and 2-3 relevant hashtags at the end. "
        "Keep it 100-200 words. NO intro like 'Here is...'. Just write the post."
    )
    content = await _generate_text_with_ai(system_prompt, f"Write a {tone} Facebook post about: {topic}")
    if not content:
        return "❌ Facebook post generate nahi ho saka."

    result = await _write_and_type_post(
        platform="Facebook",
        open_keyword="facebook",
        load_wait=6,
        post_box_prompt=(
            "Find the center coordinates of the 'What's on your mind?' input box or compose post area "
            "at the top of the Facebook home/news feed page."
        ),
        editor_prompt=(
            "The Facebook post composer dialog is now open. "
            "Find the center of the text area where the post content should be typed."
        ),
        content=content,
        screenshot_prefix="fb"
    )
    return result


@function_tool
async def facebook_publish_post(context: RunContext) -> str:
    """
    Click the 'Post' button on Facebook to publish the currently typed post.
    Call this after facebook_write_post.
    """
    return await _click_publish_button(
        platform="Facebook",
        button_prompt=(
            "Find the center coordinates of the blue 'Post' button in the Facebook post creator dialog. "
            "It is usually at the bottom right of the compose box."
        ),
        screenshot_prefix="fb"
    )


# ============================================================
# TOOL 10: Instagram — Write Caption (Web)
# ============================================================

@function_tool
async def instagram_write_caption(context: RunContext, topic: str, tone: str = "aesthetic") -> str:
    """
    Write an AI-generated Instagram caption for a post on a given topic.
    Opens Instagram web, navigates to new post, and types the caption if the post editor is open.
    Note: Instagram web upload requires an image to be selected first.

    Args:
        topic: Topic or context for the caption.
        tone: Tone — 'aesthetic', 'funny', 'motivational', 'informational', 'story'. Default 'aesthetic'.
    """
    system_prompt = (
        "You are an Instagram content strategist. Write a scroll-stopping Instagram caption. "
        "Include a hook first line, storytelling in the middle, a CTA (call to action) at the end. "
        "Add 10–15 trending hashtags at the end. Use emojis generously. NO intro text. Just the caption."
    )
    content = await _generate_text_with_ai(system_prompt, f"Write a {tone} Instagram caption about: {topic}")
    if not content:
        return "❌ Instagram caption generate nahi ho saka."

    # Open Instagram
    await open_app("instagram")
    await asyncio.sleep(5)

    # Try to find the caption box (post upload modal must already be open)
    ss_path = BASE_DIR / "data" / "ig_step1.jpg"
    _take_screenshot(ss_path)
    b64 = await _screenshot_to_b64(ss_path)

    coords_text = await _ask_vision_for_coords(
        b64,
        "Find the center coordinates of the 'Write a caption...' or caption text input area in the Instagram post creator."
    )

    if not coords_text:
        if ss_path.exists():
            ss_path.unlink()
        return (
            f"✅ Caption ready hai! Pehle Instagram pe image upload karein, phir caption area click karein.\n\n"
            f"📋 Caption:\n{content}"
        )

    x, y = _parse_coords(coords_text)
    if x and y:
        await click_at_position_tool(x, y)
        await asyncio.sleep(0.5)
        await type_text_tool(content)

    if ss_path.exists():
        ss_path.unlink()

    return f"✅ Instagram caption type ho gaya!\n\n📋 Caption:\n{content}"


# ============================================================
# TOOL 11: UNIFIED — Post to All Platforms at Once
# ============================================================

@function_tool
async def post_to_all_social(context: RunContext, topic: str) -> str:
    """
    Write and post content to ALL social media platforms (Twitter, Facebook, LinkedIn) at once.
    Each platform gets its own AI-optimized version of the post based on topic.
    
    Args:
        topic: The topic to post about on all platforms.
    """
    results = []

    # Twitter
    tw_result = await twitter_write_tweet(context, topic, tone="engaging")
    results.append(f"🐦 Twitter:\n{tw_result}")
    await asyncio.sleep(2)
    tw_pub = await twitter_publish_tweet(context)
    results.append(f"   → {tw_pub}")

    await asyncio.sleep(3)

    # Facebook
    fb_result = await facebook_write_post(context, topic, tone="friendly")
    results.append(f"\n📘 Facebook:\n{fb_result}")
    await asyncio.sleep(2)
    fb_pub = await facebook_publish_post(context)
    results.append(f"   → {fb_pub}")

    await asyncio.sleep(3)

    # LinkedIn
    li_result = await linkedin_write_post(context, topic, tone="professional")
    results.append(f"\n💼 LinkedIn:\n{li_result}")
    await asyncio.sleep(2)
    li_pub = await linkedin_publish_post(context)
    results.append(f"   → {li_pub}")

    return "\n".join(results)


# ============================================================
# TOOL 12: Open All Social Media Tabs in Chrome
# ============================================================

@function_tool
async def open_social_tabs(context: RunContext) -> str:
    """
    Open critical social media platforms (YouTube, Instagram, Facebook, Twitter/X, and LinkedIn) 
    simultaneously in Google Chrome.
    """
    urls = [
        "https://www.youtube.com",
        "https://www.instagram.com",
        "https://www.facebook.com",
        "https://www.twitter.com",
        "https://www.linkedin.com"
    ]
    
    # Using 'start chrome' directly to ensure it opens in Chrome as requested
    try:
        command = 'start chrome ' + ' '.join([f'"{url}"' for url in urls])
        await asyncio.create_subprocess_shell(command)
        return "✅ Sari social media sites (YouTube, Instagram, Facebook, Twitter, LinkedIn) Chrome mein open kar di hain! Enjoy karein."
    except Exception as e:
        return f"❌ Chrome open karne mein error aaya: {e}"
