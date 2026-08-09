import os
import psutil
import shutil
import subprocess
import httpx
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import function_tool, RunContext

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(dotenv_path=BASE_DIR / ".env")

# New Unused API Key
MISTRAL_LARGE_KEY = os.getenv("OPENROUTER_API_KEY_Mistral_Large")
if not MISTRAL_LARGE_KEY:
    MISTRAL_LARGE_KEY = os.getenv("OPENROUTER_API_KEY_GPT35")

@function_tool
async def open_application(context: RunContext, app_name: str) -> str:
    """
    Open any installed application on the laptop by its name (like 'VS Code', 'Microsoft Word', 'Chrome', 'Antigravity').
    
    Args:
        app_name: The name of the application to open.
    """
    import win32com.client
    
    # Try using Windows Shell to run standard apps
    try:
        # Simple mapping for popular aliases
        aliases = {
            "vs code": "code",
            "vscode": "code",
            "microsoft word": "winword",
            "word": "winword",
            "chrome": "chrome",
            "excel": "excel",
            "notepad": "notepad",
            "antigravity": "antigravity"
        }
        
        cmd = aliases.get(app_name.lower(), app_name.lower())
        
        # We start the application via subprocess without blocking
        subprocess.Popen(f"start {cmd}", shell=True)
        return f"✅ '{app_name}' laptop pe khol di gai hai."
        
    except Exception as e:
        return f"❌ '{app_name}' kholnay mien error aayi: {e}. Shayad ye install naa ho."

@function_tool
async def delete_application(context: RunContext, app_name: str) -> str:
    """
    Uninstall/Delete a specific application from the laptop. This is extremely dangerous.
    Uses AI (Mistral Large) to figure out the exact uninstall command strings for Windows.

    Args:
        app_name: Name of the application to uninstall completely.
    """
    try:
        # Asking AI how to safely uninstall this via windows powershell/wmic
        import httpx
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {MISTRAL_LARGE_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "zoya-agent",
            "X-Title": "Zoya OS"
        }
        
        payload = {
            "model": "mistralai/mistral-large",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a Windows System Admin. The user wants to uninstall an app completely. Provide ONLY the raw exact powershell command (using wmic or winget or powershell package) that uninstalls it silently. No markdown, no explanation."
                },
                {"role": "user", "content": f"Uninstall {app_name}"}
            ]
        }
        
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                uninstall_command = resp.json()['choices'][0]['message']['content'].strip('`').strip()
                
                # We attempt to run the uninstallation quietly
                subprocess.Popen(["powershell.exe", "-Command", uninstall_command], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return f"⚠️ '{app_name}' ko delete/uninstall karnay ka process laptop pr background mein start kardia gya hai! (Command fired: {uninstall_command[:30]}...)"
            else:
                return f"❌ AI failed to find a safe way to delete '{app_name}'."
    except Exception as e:
         return f"❌ '{app_name}' delete karnay mein issue aya: {e}"

@function_tool
async def delete_app_files(context: RunContext, folder_keyword: str) -> str:
    """
    Find and delete all residual or leftover folders files of a deleted application in C:\\Program Files or AppData.
    
    Args:
        folder_keyword: e.g., 'vscode', 'antigravity', 'adobe'.
    """
    import shutil
    import os
    
    paths_to_check = [
        os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files')),
        os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)')),
        os.environ.get('LOCALAPPDATA'),
        os.environ.get('APPDATA')
    ]
    
    deleted_paths = []
    
    try:
        for base_path in paths_to_check:
            if not base_path or not os.path.exists(base_path): continue
            
            for item in os.listdir(base_path):
                if folder_keyword.lower() in item.lower():
                    full_path = os.path.join(base_path, item)
                    try:
                        if os.path.isdir(full_path):
                            shutil.rmtree(full_path)
                        else:
                            os.remove(full_path)
                        deleted_paths.append(full_path)
                    except Exception:
                        pass # Ignore permission errors
                        
        if deleted_paths:
            return f"🗑️ In app files ko laptop se jarr se delete kardia gya hai:\n" + "\n".join(deleted_paths[:5]) + "..."
        else:
            return f"❌ '{folder_keyword}' ki koi bhi file ya folder mili hi nahi system folders mein."
            
    except Exception as e:
        return f"Error cleaning files: {e}"
