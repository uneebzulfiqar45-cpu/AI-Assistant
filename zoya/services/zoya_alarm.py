import os
import json
import asyncio
import httpx
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import function_tool, RunContext

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(dotenv_path=BASE_DIR / ".env")

SCHEDULE_FILE = BASE_DIR / "data" / "schedule.json"

# API Keys from env (matches zoya_social.py)
GPT35_KEY = os.getenv("OPENROUTER_API_KEY_GPT35")

async def _parse_time_with_ai(time_str: str) -> str:
    """Use AI to parse natural language time into ISO format."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    prompt = f"""
    Current Time: {current_time}
    Convert this natural language time description into a standard ISO 8601 format (YYYY-MM-DDTHH:MM:SS): "{time_str}"
    
    Rules:
    1. If the user mentions Urdu/Hindi terms like 'subah' (morning), 'shaam' (evening), 'raat' (night), adjust the time accordingly.
    2. 'Das baje' usually means the next 10:00 (AM or PM depends on context, defaults to next occurring).
    3. Return ONLY the ISO string. No other text.
    4. If the time is relative (e.g., '10 minutes later'), calculate it from the Current Time.
    """
    
    headers = {
        "Authorization": f"Bearer {GPT35_KEY.strip('\"')}" if GPT35_KEY else "",
        "Content-Type": "application/json",
        "HTTP-Referer": "zoya-agent",
        "X-Title": "Zoya Time Parser"
    }
    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 50
    }
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                return resp.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Time Parse Error: {e}")
    return None

@function_tool
async def set_scheduled_task(context: RunContext, time_str: str, message: str, action: str = None) -> str:
    """
    Schedule a reminder or a system action (like shutdown) for a specific time.
    
    Args:
        time_str: The time (e.g., '5 PM', '10 baje', 'kal subah 8 baje', '5 minutes later').
        message: What Zoya should say when the time arrives.
        action: Optional system action. 'shutdown' to turn off computer, 'sleep' for sleep mode.
    """
    parsed_iso = await _parse_time_with_ai(time_str)
    
    if not parsed_iso:
        return "❌ Maaf kijiye, main waqt samajh nahi saki. Dobara koshish karein."
    
    try:
        # Validate ISO
        target_dt = datetime.fromisoformat(parsed_iso)
        if target_dt < datetime.now():
            return f"❌ Yeh waqt ({parsed_iso}) toh guzar chuka hai! Future ka waqt batayein."
            
        task = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
            "target_time": parsed_iso,
            "message": message,
            "action": action,
            "status": "pending"
        }
        
        tasks = []
        if SCHEDULE_FILE.exists():
            with open(SCHEDULE_FILE, "r") as f:
                tasks = json.load(f)
        
        tasks.append(task)
        
        SCHEDULE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SCHEDULE_FILE, "w") as f:
            json.dump(tasks, f, indent=4)
            
        action_msg = f" aur action '{action}' execute hoga" if action else ""
        return f"✅ Done! Maine '{parsed_iso}' par reminder set kar diya hai: \"{message}\"{action_msg}."
        
    except Exception as e:
        return f"❌ Schedule set karne mein error aaya: {e}"

@function_tool
async def list_schedule(context: RunContext) -> str:
    """List all pending reminders and scheduled tasks."""
    if not SCHEDULE_FILE.exists():
        return "Abhi koi scheduled tasks nahi hain."
        
    try:
        with open(SCHEDULE_FILE, "r") as f:
            tasks = json.load(f)
            
        if not tasks:
            return "Abhi koi pending tasks nahi hain."
            
        res = "📋 Pending Schedules:\n"
        for t in tasks:
            action_suffix = f" [Action: {t['action']}]" if t.get('action') else ""
            res += f"- {t['target_time']}: {t['message']}{action_suffix}\n"
        return res
    except Exception as e:
        return f"❌ List karne mein error: {e}"

@function_tool
async def delete_schedule(context: RunContext, task_id: str = None) -> str:
    """Delete a task. If ID not provided, it asks for clarification."""
    if not SCHEDULE_FILE.exists():
        return "Koi schedule hi nahi hai."

    # Simple logic: for now delete the LAST one if ID not provided, or clear all?
    # Let's say it clears the most recent one by default for simplicity in voice.
    try:
        with open(SCHEDULE_FILE, "r") as f:
            tasks = json.load(f)
            
        if not tasks:
            return "Task list pehle hi khali hai."
            
        if not task_id:
            removed = tasks.pop()
            msg = f"✅ Sabse purana ya aakhri schedule '{removed['message']}' delete kar diya gaya."
        else:
            tasks = [t for t in tasks if t['id'] != task_id]
            msg = f"✅ Task id {task_id} delete kar diya gaya."
            
        with open(SCHEDULE_FILE, "w") as f:
            json.dump(tasks, f, indent=4)
        return msg
    except Exception as e:
        return f"❌ Delete karne mein error: {e}"
