import os
import base64
import httpx
from dotenv import load_dotenv
import mss
from livekit.agents import function_tool, RunContext
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(dotenv_path=BASE_DIR / ".env")

# APIs never used elsewhere yet
CLAUDE_SONNET_KEY = os.getenv("OPENROUTER_API_KEY_Claude_Sonnet")
GEMINI_PRO_KEY = os.getenv("OPENROUTER_API_KEY_Gemini_Pro")
CLAUDE_HAIKU_KEY = os.getenv("OPENROUTER_API_KEY_Claude_Haiku")

@function_tool
async def save_screen_capture(context: RunContext, save_path: str = None) -> str:
    """
    Take a screenshot of the computer screen and save it permanently where the user tells you to.
    Use this when the user says "take a screenshot and save it to..." or "laptop ki picture lo".

    Args:
        save_path: Optional. The absolute path where the user wants to save the file (e.g. 'c:\\Users\\uneeb\\Desktop\\MyPic.png'). If user doesn't provide a location, ask them where to save it or use the default 'd:\\ai\\data\\screenshots\\capture.png'.
    """
    import time
    if not save_path:
        # Default fallback only if not specified
        save_dir = BASE_DIR / "data" / "screenshots"
        save_dir.mkdir(parents=True, exist_ok=True)
        save_path = str(save_dir / f"capture_{int(time.time())}.png")
        
    # Ensure directory of the specific file path exists
    try:
        final_path = Path(save_path)
        final_path.parent.mkdir(parents=True, exist_ok=True)
        
        with mss.mss() as sct:
            sct.shot(output=str(final_path))
        return f"✅ Screenshot permanently {final_path} mein save ho gaya hai."
    except Exception as e:
        return f"❌ Screenshot save karne mein error aai: {e}"

@function_tool
async def take_screenshot_and_read(context: RunContext, prompt: str = "Is screen ko dekhein aur mujhe batain screen par kya chal raha hai?", save_path: str = None) -> str:
    """
    Take a live screenshot of the computer screen instantly, read it, and explain it or extract text from it. 
    Use this when the user says "Read the screen" or "Dekho meri screen pe kya hai".

    Args:
        prompt: Default is "describe the screen", but you can pass specific OCR queries.
        save_path: Set an absolute path (e.g., 'C:\\myfolder\\pic.jpg') if user also wants this read image to be saved permanently. If empty, the image will be deleted after reading.
    """
    keys_to_try = [
        (CLAUDE_SONNET_KEY, "anthropic/claude-3.5-sonnet"),
        (GEMINI_PRO_KEY, "google/gemini-1.5-pro"),
        (CLAUDE_HAIKU_KEY, "anthropic/claude-3-haiku")
    ]
    
    screenshot_path = BASE_DIR / "data" / "live_screenshot.jpg"
    BASE_DIR.joinpath("data").mkdir(exist_ok=True)
    
    try:
        # Take screenshot silently
        with mss.mss() as sct:
            sct.shot(output=str(screenshot_path))
            
        # Encode to Base64
        with open(screenshot_path, "rb") as img_file:
            base64_img = base64.b64encode(img_file.read()).decode('utf-8')
            
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        last_err = ""
        for key, model_id in keys_to_try:
            if not key:
                continue
                
            headers = {
                "Authorization": f"Bearer {key.strip('\"')}",
                "Content-Type": "application/json",
                "HTTP-Referer": "zoya-agent",
                "X-Title": "Zoya Vision"
            }
            
            payload = {
                "model": model_id,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"You are Zoya Vision. Action: {prompt}. Reply in Roman Urdu compactly."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_img}"
                                }
                            }
                        ]
                    }
                ]
            }
            
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    if not save_path:
                        os.remove(screenshot_path)
                    else:
                        import shutil
                        final_save = Path(save_path)
                        final_save.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(screenshot_path), str(final_save))
                    return f"✅ [Model: {model_id}] {resp.json()['choices'][0]['message']['content'].strip()}"
                else:
                    last_err = f"Status {resp.status_code}: {resp.text}"
                    continue # Try next key
                    
        if not save_path and os.path.exists(screenshot_path):
            os.remove(screenshot_path)
        return f"❌ Screen read / Vision Error from all keys. Last error: {last_err}"
            
    except Exception as e:
        if not save_path and os.path.exists(screenshot_path):
            os.remove(screenshot_path)
        return f"❌ Screen read Exception: {e}"
