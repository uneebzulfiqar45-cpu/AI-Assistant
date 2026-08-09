import os
import subprocess
import logging
import sys
import asyncio
from fuzzywuzzy import process

try:
    from livekit.agents import function_tool
except ImportError:
    def function_tool(func): 
        return func

try:
    import win32gui
    import win32con
except ImportError:
    win32gui = None
    win32con = None

try:
    import pygetwindow as gw
except ImportError:
    gw = None

# Setup encoding and logger
sys.stdout.reconfigure(encoding='utf-8')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# App command map — verified paths from actual system scan
# Store apps: shell:AppsFolder\AppID | Regular apps: full .exe path | URLs: https://...
APP_MAPPINGS = {
    # === System Tools ===
    # === System Tools ===
    "notepad":        "notepad.exe",
    "calculator":     "shell:AppsFolder\\Microsoft.WindowsCalculator_8wekyb3d8bbwe!App",
    "paint":          "mspaint.exe",
    "control panel":  "control",
    "settings":       "ms-settings:",
    "task manager":   "taskmgr",
    "command prompt": "cmd",
    "camera":         "shell:AppsFolder\\Microsoft.WindowsCamera_8wekyb3d8bbwe!App",
    "clock":          "shell:AppsFolder\\Microsoft.WindowsAlarms_8wekyb3d8bbwe!App",
    "photos":         "shell:AppsFolder\\Microsoft.Windows.Photos_8wekyb3d8bbwe!App",
    "store":          "shell:AppsFolder\\Microsoft.WindowsStore_8wekyb3d8bbwe!App",

    # === Browsers ===
    "chrome":         "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "edge":           "msedge.exe",

    # === Drives & Basic Locations ===
    "d":              "D:\\",
    "d drive":        "D:\\",
    "drive d":        "D:\\",
    "d:":             "D:\\",
    "c":              "C:\\",
    "c drive":        "C:\\",
    "drive c":        "C:\\",
    "c:":             "C:\\",
    "my pc":          "explorer.exe shell:MyComputerFolder",
    "this pc":        "explorer.exe shell:MyComputerFolder",
    "desktop":        "C:\\Users\\uneeb\\OneDrive\\Desktop",
    "downloads":      "C:\\Users\\uneeb\\Downloads",
    "download":       "C:\\Users\\uneeb\\Downloads",
    "documents":      "C:\\Users\\uneeb\\OneDrive\\Documents",
    "document":       "C:\\Users\\uneeb\\OneDrive\\Documents",
    "pictures":       "C:\\Users\\uneeb\\OneDrive\\Pictures",
    "picture":        "C:\\Users\\uneeb\\OneDrive\\Pictures",
    "p":              "C:\\Users\\uneeb\\OneDrive\\Pictures",
    "screenshots":    "C:\\Users\\uneeb\\OneDrive\\Pictures\\Screenshots",
    "screenshot":     "C:\\Users\\uneeb\\OneDrive\\Pictures\\Screenshots",
    "camera roll":    "C:\\Users\\uneeb\\OneDrive\\Pictures\\Camera Roll",
    "v":              "C:\\Users\\uneeb\\Videos",
    "videos":         "C:\\Users\\uneeb\\Videos",
    "video":          "C:\\Users\\uneeb\\Videos",
    "music":          "C:\\Users\\uneeb\\Music",

    # === User Folders (D Drive) ===
    "4th semester":   "D:\\4th semester",
    "ai folder":      "D:\\ai",
    "ai project":     "D:\\AI project",
    "excel research": "D:\\excel research",
    "final paper":    "D:\\final paper",
    "horse folder":   "D:\\horse",
    "house folder":   "D:\\house",
    "project uneeb":  "D:\\project uneeb",

    # === Microsoft Office ===
    "word":           "shell:AppsFolder\\Microsoft.Office.WINWORD.EXE.15",
    "excel":          "shell:AppsFolder\\Microsoft.Office.EXCEL.EXE.15",
    "powerpoint":     "shell:AppsFolder\\Microsoft.Office.POWERPNT.EXE.15",

    # === Apps ===
    "whatsapp":       "shell:AppsFolder\\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App",
    "zoom":           "C:\\Users\\uneeb\\AppData\\Roaming\\Zoom\\bin\\Zoom.exe",
    "vs code":        "D:\\Microsoft VS Code\\Code.exe",
    "vscode":         "D:\\Microsoft VS Code\\Code.exe",
    "steam":          "D:\\steam\\steam.exe",
    "xampp":          "D:\\xamp\\xampp-control.exe",
    "github desktop": "C:\\Users\\uneeb\\AppData\\Local\\GitHubDesktop\\GitHubDesktop.exe",
    "vlc":            "C:\\Program Files (x86)\\VideoLAN\\VLC\\vlc.exe",

    # === Social Media (Web Fallbacks) ===
    "youtube":        "https://www.youtube.com",
    "facebook":       "https://www.facebook.com",
    "instagram":      "https://www.instagram.com",
    "twitter":        "https://x.com",
    "x":              "https://x.com",
    "linkedin":       "https://www.linkedin.com",
}

# -------------------------
# Global focus utility
# -------------------------
# Global focus utility
# -------------------------
async def focus_window(title_keyword: str) -> bool:
    if not gw:
        logger.warning("⚠ pygetwindow")
        return False

    await asyncio.sleep(1.5)  # Give time for window to appear
    title_keyword = title_keyword.lower().strip()

    for window in gw.getAllWindows():
        if title_keyword in window.title.lower():
            if window.isMinimized:
                window.restore()
            window.activate()
            return True
    return False

# Index files/folders
async def index_items(base_dirs):
    item_index = []
    for base_dir in base_dirs:
        for root, dirs, files in os.walk(base_dir):
            for d in dirs:
                item_index.append({"name": d, "path": os.path.join(root, d), "type": "folder"})
            for f in files:
                item_index.append({"name": f, "path": os.path.join(root, f), "type": "file"})
    logger.info(f"✅ Indexed {len(item_index)} items.")
    return item_index

async def search_item(query, index, item_type):
    filtered = [item for item in index if item["type"] == item_type]
    choices = [item["name"] for item in filtered]
    if not choices:
        return None
    best_match, score = process.extractOne(query, choices)
    logger.info(f"🔍 Matched '{query}' to '{best_match}' with score {score}")
    if score > 70:
        for item in filtered:
            if item["name"] == best_match:
                return item
    return None

# File/folder actions
async def open_folder(path):
    try:
        os.startfile(path) if os.name == 'nt' else subprocess.call(['xdg-open', path])
        # Smart focus for drives and folders
        focus_title = os.path.basename(path)
        if ":" in path and len(path) <= 3: # It's a drive root like D:\
            drive_letter = path[0].upper()
            focus_title = f"({drive_letter}:)" # Windows explorer titles drives like "Local Disk (D:)"
        
        await focus_window(focus_title)
    except Exception as e:
        logger.error(f"❌ File open karne mein error aya: {e}")

async def play_file(path):
    try:
        os.startfile(path) if os.name == 'nt' else subprocess.call(['xdg-open', path])
        await focus_window(os.path.basename(path))
    except Exception as e:
        logger.error(f"❌ File open karne mein error aya: {e}")

async def create_folder(path):
    try:
        os.makedirs(path, exist_ok=True)
        return f"✅ Folder create ho gaya: {path}"
    except Exception as e:
        return f"❌ File create karne mein error aya: {e}"

async def rename_item(old_path, new_path):
    try:
        os.rename(old_path, new_path)
        return f"✅ Naam badalkar {new_path} kar diya gaya."
    except Exception as e:
        return f"❌ Naam badalna fail ho gaya: {e}"

async def delete_item(path):
    try:
        if os.path.isdir(path):
            os.rmdir(path)
        else:
            os.remove(path)
        return f"🗑️ Deleted: {path}"
    except Exception as e:
        return f"❌ Delete nahi hua: {e}"

# App control
@function_tool
async def open_app(app_title: str) -> str:
    app_title = app_title.lower().strip()

    # Web fallbacks if desktop app truly fails
    web_fallbacks = {
        "whatsapp": "https://web.whatsapp.com",
        "youtube": "https://www.youtube.com",
        "facebook": "https://www.facebook.com",
        "instagram": "https://www.instagram.com",
        "twitter": "https://x.com"
    }

    app_command = APP_MAPPINGS.get(app_title, app_title)

    try:
        # 1. URL handling (Handles social media now)
        if app_command.startswith("http"):
            # Use 'start chrome' if available, otherwise default
            chrome_path = APP_MAPPINGS.get("chrome")
            if chrome_path and os.path.exists(chrome_path):
                subprocess.Popen(f'"{chrome_path}" "{app_command}"', shell=True)
            else:
                os.startfile(app_command)
            return f"🌐 {app_title} browser mein open kiya gaya."

        # 2. shell: URIs (Store Apps)
        if app_command.startswith("shell:"):
            subprocess.Popen(f'explorer.exe "{app_command}"', shell=True)
            return f"✅ {app_title} launch kiya gaya (Store App)."

        # 3. Direct Explorer calls (Drives/Folders/Files)
        if ":" in app_command or "\\" in app_command:
            p = app_command.strip('"')
            if os.path.exists(p):
                os.startfile(p)
                return f"📁 {app_title} ({p}) open kiya gaya."

        # 4. Smart Folder Search Fallback
        search_roots = ["D:\\", "C:\\Users\\uneeb\\OneDrive\\Desktop", "C:\\Users\\uneeb\\Downloads"]
        for root in search_roots:
            potential_path = os.path.join(root, app_title)
            if os.path.isdir(potential_path):
                os.startfile(potential_path)
                return f"🔍 Mapping mein nahi mila, lekin '{app_title}' folder {root} mein mil gaya aur open kar diya."

        # 5. Standard Commands (with validity check to avoid Windows dialogs)
        # We only 'start' it if it's a known mapped app or a common exe
        if app_title in APP_MAPPINGS or app_command.endswith(".exe"):
            subprocess.Popen(f'start "" "{app_command}"', shell=True)
            await asyncio.sleep(2)
            await focus_window(app_title)
            return f"🚀 {app_title} launch kiya gaya."
        else:
            # If we don't know what it is, don't let Windows throw a dialog
            # Instead, trigger the web fallback if it's a social site, or return error
            if app_title in web_fallbacks:
                fallback_url = web_fallbacks[app_title]
                chrome_path = APP_MAPPINGS.get("chrome")
                if chrome_path and os.path.exists(chrome_path):
                     subprocess.Popen(f'"{chrome_path}" "{fallback_url}"', shell=True)
                else:
                    os.startfile(fallback_url)
                return f"⚠️ {app_title} desktop app nahi mili, browser mein khola gaya."
            
            return f"❌ {app_title} naam ki koi app ya mapping nahi mili. Zoya ne command block kar di taake error na aaye."

    except Exception as e:
        return f"❌ {app_title} launch nahi ho paya: {e}"

@function_tool
async def close(window_title: str) -> str:
    if not win32gui:
        return "❌ win32gui"

    def enumHandler(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            if window_title.lower() in win32gui.GetWindowText(hwnd).lower():
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)

    win32gui.EnumWindows(enumHandler, None)
    return f"❌ Window band ho gayi hai: {window_title}"

# Jarvis command logic
@function_tool
async def folder_file(command: str) -> str:
    folders_to_index = ["D:/"]
    index = await index_items(folders_to_index)
    command_lower = command.lower().strip()

    # Special check for Drives directly in folder_file
    drive_map = {
        "d drive": "D:\\",
        "d:": "D:\\",
        "d": "D:\\",
        "c drive": "C:\\",
        "c:": "C:\\",
        "c": "C:\\"
    }
    
    # Try to see if they just want a drive
    for k, v in drive_map.items():
        if command_lower == k or command_lower == f"open {k}" or command_lower == f"go to {k}":
            await open_folder(v)
            return f"✅ Drive root opened: {v}"

    if "create folder" in command_lower:
        folder_name = command.replace("create folder", "").strip()
        path = os.path.join("D:/", folder_name)
        return await create_folder(path)

    if "rename" in command_lower:
        parts = command_lower.replace("rename", "").strip().split("to")
        if len(parts) == 2:
            old_name = parts[0].strip()
            new_name = parts[1].strip()
            item = await search_item(old_name, index, "folder")
            if item:
                new_path = os.path.join(os.path.dirname(item["path"]), new_name)
                return await rename_item(item["path"], new_path)
        return "❌ rename command valid nahi hai."

    if "delete" in command_lower:
        item = await search_item(command, index, "folder") or await search_item(command, index, "file")
        if item:
            return await delete_item(item["path"])
        return "❌ Delete karne ke liye item nahi mila."

    if "folder" in command_lower or "open folder" in command_lower:
        item = await search_item(command, index, "folder")
        if item:
            await open_folder(item["path"])
            return f"✅ Folder opened: {item['name']}"
        return "❌ Folder nahi mila."

    item = await search_item(command, index, "file")
    if item:
        await play_file(item["path"])
        return f"✅ File opened: {item['name']}"

    return "⚠ Kuch bhi match nahi hua."
