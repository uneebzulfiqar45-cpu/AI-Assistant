"""
Zoya System Master
===================
Computer ki taaqat Zoya ke hathon mein — 
Shutdown, Sleep, Volume, Brightness aur Hardware control.
"""

import os
import ctypes
import psutil
import subprocess
from datetime import datetime
from pathlib import Path
from livekit.agents import function_tool, RunContext

def log_hardware_action(action: str):
    """Log hardware control actions to the central control_log.txt"""
    # Using relative path to match keyboard_mouse_CTRL logic
    with open("control_log.txt", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()}: [HARDWARE] {action}\n")

# ─── Power Management (Direct C-calls & CMD) ──────────────────────────────────

@function_tool
async def control_power(context: RunContext, action: str) -> str:
    """
    Laptop ki power state badlo (Shutdown, Restart, Sleep, Hibernate).
    
    Args:
        action: 'shutdown', 'restart', 'sleep', 'hibernate'
    """
    try:
        if action == "shutdown":
            os.system("shutdown /s /t 0")
            return "✅ Laptop shutdown ho raha hai. Khuda Hafiz!"
        elif action == "restart":
            os.system("shutdown /r /t 0")
            return "✅ Laptop restart ho raha hai. Main thori dair mein wapas aati hoon."
        elif action == "sleep":
            # Native C-call for Sleep
            ctypes.windll.powrprof.SetSuspendState(0, 1, 0)
            return "✅ Laptop sleep mode mein chala gaya hai. Zzz..."
        elif action == "hibernate":
            os.system("shutdown /h")
            return "✅ Laptop hibernate ho raha hai."
        else:
            return f"❌ '{action}' valid action nahi hai. Use shutdown, restart, sleep, or hibernate."
    except Exception as e:
        return f"❌ Power control fail hua: {e}"

# ─── Hardware Levels (Volume, Brightness, Battery) ───────────────────────────

@function_tool
async def get_battery_info(context: RunContext) -> str:
    """
    Laptop ki battery percentage aur charging status check karo.
    """
    battery = psutil.sensors_battery()
    if not battery:
        return "❌ Battery information nahi mil saki."
    
    percent = battery.percent
    plugged = battery.power_plugged
    status = "Charging pe hai ⚡" if plugged else "Battery pe chal raha hai 🔋"
    
    if percent < 20 and not plugged:
        msg = f"⚠️ Battery sirf {percent}% hai aur charging par nahi hai! Jaldi se charger lagayein."
    else:
        msg = f"🔋 Battery {percent}% hai aur {status}."
        
    return msg

@function_tool
async def set_laptop_brightness(context: RunContext, level: int) -> str:
    """
    Laptop ki brightness kam ya zyada karo.
    
    Args:
        level: Brightness percentage (0 to 100)
    """
    try:
        # PowerShell Native WMI Method (Most reliable for Win 10/11)
        cmd = f"powershell -Command \"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, {level})\""
        subprocess.run(cmd, shell=True, check=True, capture_output=True)
        log_hardware_action(f"Brightness set to {level}%")
        return f"🔆 Brightness {level}% par set ho gayi hai."
    except Exception as e:
        log_hardware_action(f"Brightness Error: {e}")
        return f"❌ Brightness set nahi ho saki. Driver issues ho saktay hain."

@function_tool
async def set_laptop_volume(context: RunContext, level: int) -> str:
    """
    Laptop ki volume percentage set karo.
    
    Args:
        level: Volume percentage (0 to 100)
    """
    try:
        # Robust and completely native way to set Windows Volume:
        # Spam Volume Down 50 times to guarantee it reaches 0%, then Volume Up natively.
        # We MUST use a tiny interval otherwise the Windows Audio service drops the rapid keys!
        import pyautogui
        import time
        
        # Mute to 0
        pyautogui.press("volumedown", presses=50, interval=0.02)
        
        # Raise to target
        target_presses = level // 2
        if target_presses > 0:
            pyautogui.press("volumeup", presses=target_presses, interval=0.02)
            
        subprocess.run(f"powershell -Command \"Write-Host 'Volume set to {level}'\"", shell=True, check=False) # Dummy for completion
        
        log_hardware_action(f"Volume level set to {level}%")
        return f"🔊 Volume {level}% par set ho gaya hai."
    except Exception as e:
        log_hardware_action(f"Volume Error: {e}")
        return f"❌ Volume control fail hua."

# ─── Connectivity (WiFi, BT, Airplane) ──────────────────────────────────────

@function_tool
async def toggle_wifi(context: RunContext, state: bool) -> str:
    """
    WiFi ko on ya off karo.
    """
    cmd_state = "enabled" if state else "disabled"
    # Note: Requires Admin usually, or netsh disconnect
    try:
        if state:
            os.system(f'netsh interface set interface name="Wi-Fi" admin=enabled')
            return "📶 Wi-Fi on ho gaya."
        else:
            os.system(f'netsh interface set interface name="Wi-Fi" admin=disabled')
            return "📶 Wi-Fi off ho gaya."
    except Exception as e:
        return f"❌ WiFi toggle fail hua: {e}"

@function_tool
async def toggle_battery_saver(context: RunContext, state: bool) -> str:
    """
    Laptop ka Battery Saver (Power Saver plan) on ya off karo.
    """
    # GUIDs are standard for Balanced and Power Saver
    POWER_SAVER_GUID = "a1841308-3541-4fab-bc81-f71556f20b4a"
    BALANCED_GUID = "381b4222-f694-41f0-9685-ff5bb260df2e"
    
    selected_guid = POWER_SAVER_GUID if state else BALANCED_GUID
    action_name = "Battery Saver On" if state else "Balanced Mode (Battery Saver Off)"
    
    try:
        os.system(f"powercfg /setactive {selected_guid}")
        return f"🔋 {action_name} ho gaya hai."
    except Exception as e:
        return f"❌ Battery saver toggle fail hua: {e}"

@function_tool
async def open_hardware_settings(context: RunContext, topic: str) -> str:
    """
    Bluetooth, WiFi, ya Airplane Mode ki settings kholo taakay main wahan se toggle kar sakoon.
    
    Args:
        topic: 'bluetooth', 'wifi', 'airplane', 'display'
    """
    uris = {
        "bluetooth": "ms-settings:bluetooth",
        "wifi": "ms-settings:network-wifi",
        "airplane": "ms-settings:network-airplanemode",
        "display": "ms-settings:display"
    }
    uri = uris.get(topic.lower(), "ms-settings:home")
    os.system(f"start {uri}")
    return f"⚙️ {topic.capitalize()} settings khul gayi hain. Main screen dekh kar button toggle kar sakti hoon."
