import pyautogui
import asyncio
import time
from datetime import datetime
from pynput.keyboard import Key, Controller as KeyboardController
from pynput.mouse import Button, Controller as MouseController
from typing import List
from livekit.agents import function_tool

# ---------------------
# SafeController Class
# ---------------------
class SafeController:
    def __init__(self):
        self.active = False
        self.activation_time = None
        self.keyboard = KeyboardController()
        self.mouse = MouseController()
        self.valid_keys = set("abcdefghijklmnopqrstuvwxyz1234567890")
        self.special_keys = {
            "enter": Key.enter, "space": Key.space, "tab": Key.tab,
            "shift": Key.shift, "ctrl": Key.ctrl, "alt": Key.alt,
            "esc": Key.esc, "backspace": Key.backspace, "delete": Key.delete,
            "up": Key.up, "down": Key.down, "left": Key.left, "right": Key.right,
            "caps_lock": Key.caps_lock, "cmd": Key.cmd, "win": Key.cmd,
            "home": Key.home, "end": Key.end,
            "page_up": Key.page_up, "page_down": Key.page_down
        }

    def resolve_key(self, key):
        return self.special_keys.get(key.lower(), key)

    def log(self, action: str):
        with open("control_log.txt", "a", encoding="utf-8") as f:
            f.write(f"{datetime.now()}: {action}\n")

    def activate(self, token=None):
        if token != "my_secret_token":
            self.log("Activation attempt failed.")
            return
        self.active = True
        self.activation_time = time.time()
        self.log("Controller auto-activated.")

    def deactivate(self):
        self.active = False
        self.log("Controller auto-deactivated.")

    def is_active(self):
        return self.active

    async def move_cursor(self, direction: str, distance: int = 100):
        if not self.is_active(): return "🛑 Controller is inactive."
        try:
            # pyautogui.moveRel is perfect for "jolting" the mouse during pranks
            if direction == "left": pyautogui.moveRel(-distance, 0, duration=0.2)
            elif direction == "right": pyautogui.moveRel(distance, 0, duration=0.2)
            elif direction == "up": pyautogui.moveRel(0, -distance, duration=0.2)
            elif direction == "down": pyautogui.moveRel(0, distance, duration=0.2)
        except Exception:
            # Fallback to pynput
            x, y = self.mouse.position
            if direction == "left": self.mouse.position = (x - distance, y)
            elif direction == "right": self.mouse.position = (x + distance, y)
            elif direction == "up": self.mouse.position = (x, y - distance)
            elif direction == "down": self.mouse.position = (x, y + distance)
            
        await asyncio.sleep(0.2)
        self.log(f"Mouse moved {direction} by {distance}px")
        return f"🖱️ Moved mouse {direction}."

    async def mouse_click(self, button: str = "left"):
        if not self.is_active(): return "🛑 Controller is inactive."
        if button == "left": self.mouse.click(Button.left, 1)
        elif button == "right": self.mouse.click(Button.right, 1)
        elif button == "double": self.mouse.click(Button.left, 2)
        await asyncio.sleep(0.2)
        self.log(f"Mouse clicked: {button}")
        return f"🖱️ {button.capitalize()} click."

    async def scroll_cursor(self, direction: str, amount: int = 10):
        if not self.is_active(): return "🛑 Controller is inactive."
        try:
            # PyAutoGUI scroll is more reliable for general UI on Windows
            scroll_amount = amount * 100
            if direction == "up":
                pyautogui.scroll(scroll_amount)
            elif direction == "down":
                pyautogui.scroll(-scroll_amount)
        except Exception as e:
            # Fallback to pynput
            if direction == "up": self.mouse.scroll(0, amount)
            elif direction == "down": self.mouse.scroll(0, -amount)
        
        await asyncio.sleep(0.2)
        self.log(f"Mouse scrolled {direction} by {amount}")
        return f"🖱️ Scrolled {direction}"

    async def type_text(self, text: str):
        if not self.is_active(): return "🛑 Controller is inactive."
        for char in text:
            if not char.isprintable():
                continue
            try:
                self.keyboard.press(char)
                self.keyboard.release(char)
                await asyncio.sleep(0.05)
            except Exception:
                continue
        self.log(f"Typed text: {text}")
        return f"⌨️ Typed: {text}"

    async def press_key(self, key: str):
        if not self.is_active(): return "🛑 Controller is inactive."
        k = key.lower()
        # Aliases for convenience
        if k in ["win", "windows", "super", "cmd", "command"]:
            k = "win"
        if k == "caps_lock":
            k = "capslock"
        if k in ["add", "plus", "+"]:
            k = "add"      # Keypad +
        if k in ["subtract", "minus", "-"]:
            k = "subtract" # Keypad -
        if k in ["vol_up", "volume_up"]:
            k = "volumeup"
        if k in ["vol_down", "volume_down"]:
            k = "volumedown"
        if k in ["mute", "volume_mute"]:
            k = "volumemute"
        if k in ["print_screen", "screenshot", "prtsc"]:
            k = "printscreen"
        if k in ["playpause", "media_play_pause", "pause", "resume"]:
            k = "playpause"
        if k in ["stop", "media_stop", "stop_music"]:
            k = "mediastop"
        if k in ["next", "media_next", "next_track"]:
            k = "nexttrack"
        if k in ["prev", "media_previous", "prev_track"]:
            k = "prevtrack"
        
        try:
            pyautogui.press(k)
        except Exception as e:
            # Fallback to pynput if pyautogui fails for some specific keys
            try:
                k_pynput = self.resolve_key(key)
                self.keyboard.press(k_pynput)
                self.keyboard.release(k_pynput)
            except Exception as e2:
                return f"❌ Failed key: {key} — {e} | {e2}"
        
        await asyncio.sleep(0.2)
        self.log(f"Pressed key: {key}")
        return f"⌨️ Key '{key}' pressed."

    async def press_hotkey(self, keys: List[str]):
        if not self.is_active(): return "🛑 Controller is inactive."
        
        # Standardize keys for pyautogui
        standard_keys = []
        for k in keys:
            kl = k.lower()
            if kl in ["win", "windows", "super", "cmd", "command"]:
                standard_keys.append("win")
            else:
                standard_keys.append(kl)

        try:
            pyautogui.hotkey(*standard_keys)
        except Exception as e:
            # Fallback to pynput
            try:
                resolved = [self.resolve_key(k) for k in keys]
                for k in resolved: self.keyboard.press(k)
                for k in reversed(resolved): self.keyboard.release(k)
            except Exception as e2:
                return f"❌ Failed hotkey: {' + '.join(keys)} — {e} | {e2}"

        await asyncio.sleep(0.3)
        self.log(f"Pressed hotkey: {' + '.join(keys)}")
        return f"⌨️ Hotkey {' + '.join(keys)} pressed."

    async def control_volume(self, action: str):
        if not self.is_active(): return "🛑 Controller is inactive."
        try:
            # Using PowerShell to send hardware-level keycodes (Reliable)
            # 175 = Volume Up, 174 = Volume Down, 173 = Mute
            code = 175 if action == "up" else (174 if action == "down" else 173)
            import subprocess
            cmd = f"powershell -Command \"(New-Object -ComObject WScript.Shell).SendKeys([char]{code})\""
            subprocess.run(cmd, shell=True, check=False)
            self.log(f"Volume control (PS): {action}")
            return f"🔊 Volume {action}."
        except Exception:
            # Fallback to pyautogui
            if action == "up": pyautogui.press("volumeup")
            elif action == "down": pyautogui.press("volumedown")
            elif action == "mute": pyautogui.press("volumemute")
            self.log(f"Volume control (Fallback): {action}")
            return f"🔊 Volume {action}."

    async def swipe_gesture(self, direction: str):
        if not self.is_active(): return "🛑 Controller is inactive."
        screen_width, screen_height = pyautogui.size()
        x, y = screen_width // 2, screen_height // 2
        try:
            # Standardizing swiping with pyautogui for better UI interaction
            if direction == "up": 
                pyautogui.moveTo(x, y + 200)
                pyautogui.dragRel(0, -400, duration=0.5)
            elif direction == "down": 
                pyautogui.moveTo(x, y - 200)
                pyautogui.dragRel(0, 400, duration=0.5)
            elif direction == "left": 
                pyautogui.moveTo(x + 200, y)
                pyautogui.dragRel(-400, 0, duration=0.5)
            elif direction == "right": 
                pyautogui.moveTo(x - 200, y)
                pyautogui.dragRel(400, 0, duration=0.5)
        except Exception as e:
            self.log(f"Swipe Error: {e}")
            pass
        await asyncio.sleep(0.5)
        self.log(f"Swipe gesture: {direction}")
        return f"🖱️ Swipe {direction} done."

    async def move_and_click(self, x: int, y: int, button: str = "left"):
        if not self.is_active(): return "🛑 Controller is inactive."
        try:
            # 1. Move cautiously
            pyautogui.moveTo(x, y, duration=0.2)
            await asyncio.sleep(0.1)
            
            # 2. Click using PyAutoGUI (Stronger than pynput for many Windows apps)
            if button == "left":
                pyautogui.mouseDown(x, y, button='left')
                await asyncio.sleep(0.1)
                pyautogui.mouseUp(x, y, button='left')
            elif button == "right":
                pyautogui.mouseDown(x, y, button='right')
                await asyncio.sleep(0.1)
                pyautogui.mouseUp(x, y, button='right')
            elif button == "double":
                pyautogui.doubleClick(x, y)
            
            # 3. Micro-jitter for focus confirmation (only if needed, but here as a safety)
            # pyautogui.moveRel(1, 1); pyautogui.moveRel(-1, -1)
            
        except Exception as e:
            # Fallback to pynput if pyautogui fails
            self.mouse.position = (x, y)
            await asyncio.sleep(0.3)
            if button == "left": self.mouse.click(Button.left, 1)
            elif button == "right": self.mouse.click(Button.right, 1)
            elif button == "double": self.mouse.click(Button.left, 2)
            
        await asyncio.sleep(0.2)
        self.log(f"Mouse moved to ({x}, {y}) and clicked: {button}")
        return f"🖱️ Moved to ({x}, {y}) and {button} clicked."

# ------------------------------
# LiveKit Tool Wrappers Section
# ------------------------------

controller = SafeController()

async def with_temporary_activation(fn, *args, **kwargs):
    print(f"🔍 TEMP ACTIVATION: {fn.__name__} | args: {args}")
    controller.activate("my_secret_token")
    result = await fn(*args, **kwargs)
    await asyncio.sleep(2)
    controller.deactivate()
    return result

@function_tool
async def move_cursor_tool(direction: str, distance: int = 100):
    return await with_temporary_activation(controller.move_cursor, direction, distance)

@function_tool
async def mouse_click_tool(button: str = "left"):
    return await with_temporary_activation(controller.mouse_click, button)

@function_tool
async def scroll_cursor_tool(direction: str, amount: int = 10):
    return await with_temporary_activation(controller.scroll_cursor, direction, amount)

@function_tool
async def type_text_tool(text: str):
    return await with_temporary_activation(controller.type_text, text)

@function_tool
async def press_key_tool(key: str):
    return await with_temporary_activation(controller.press_key, key)

@function_tool
async def press_hotkey_tool(keys: List[str]):
    return await with_temporary_activation(controller.press_hotkey, keys)

@function_tool
async def control_volume_tool(action: str):
    return await with_temporary_activation(controller.control_volume, action)

@function_tool
async def swipe_gesture_tool(direction: str):
    return await with_temporary_activation(controller.swipe_gesture, direction)

@function_tool
async def click_at_position_tool(x: int, y: int, button: str = "left"):
    """
    Move the mouse to a specific (x, y) coordinate and click.
    Useful for UI interaction when vision provides coordinates.
    """
    return await with_temporary_activation(controller.move_and_click, x, y, button)

@function_tool
async def stop_media_tool():
    """
    Sends a global 'Media Stop' command to the system. 
    Useful for immediately stopping YouTube, Spotify, or any media playback.
    """
    return await with_temporary_activation(controller.press_key, "mediastop")

@function_tool
async def play_pause_media_tool():
    """
    Sends a global 'Media Play/Pause' command to the system.
    """
    return await with_temporary_activation(controller.press_key, "playpause")

@function_tool
async def close_browser_tab(tab_name: str = "") -> str:
    """
    Closes a browser tab. If tab_name is provided, it cycles through open tabs 
    in the active browser window using Ctrl+Tab to find and close a tab with a matching title.
    If tab_name is empty or 'current', it closes the currently active tab.
    """
    import win32gui
    import time
    
    tab_name = tab_name.lower().strip()
    
    # Activate the controller first (required for safe controller hotkeys)
    controller.activate("my_secret_token")
    
    try:
        # Get the current active window
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            controller.deactivate()
            return "❌ Koi active window nahi mili."
            
        initial_title = win32gui.GetWindowText(hwnd).lower()
        
        # Check if we are in a browser window
        browser_keywords = ["chrome", "edge", "firefox", "opera", "browser"]
        is_browser = any(k in initial_title for k in browser_keywords)
        if not is_browser:
            controller.deactivate()
            return f"❌ Active window ek browser nahi lagti: '{win32gui.GetWindowText(hwnd)}'"
            
        if not tab_name or tab_name in ["current", "this", "active"]:
            # Close current tab
            await controller.press_hotkey(["ctrl", "w"])
            controller.deactivate()
            return "✅ Active browser tab ko close kar diya gaya."
            
        # Cycle through tabs to find tab_name (max 12 attempts to avoid infinite loops)
        found = False
        for attempt in range(12):
            current_title = win32gui.GetWindowText(win32gui.GetForegroundWindow()).lower()
            if tab_name in current_title:
                # Close the matching tab
                await controller.press_hotkey(["ctrl", "w"])
                found = True
                break
                
            # Press Ctrl + Tab to switch to next tab
            await controller.press_hotkey(["ctrl", "tab"])
            await asyncio.sleep(0.4) # Give a moment for browser to load tab and update title
            
            # If we cycled back to initial title, stop
            new_title = win32gui.GetWindowText(win32gui.GetForegroundWindow()).lower()
            if new_title == initial_title and attempt > 0:
                break
                
        controller.deactivate()
        if found:
            return f"✅ '{tab_name}' tab ko successfully dhoond kar close kar diya gaya."
        else:
            return f"❌ Active browser mein '{tab_name}' naam ki koi tab nahi mili."
            
    except Exception as e:
        controller.deactivate()
        return f"❌ Tab close karne mein error aya: {e}"


