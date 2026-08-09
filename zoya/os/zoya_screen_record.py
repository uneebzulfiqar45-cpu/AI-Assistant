import cv2
import numpy as np
import mss
import time
import os
import asyncio
from pathlib import Path
from livekit.agents import function_tool, RunContext

BASE_DIR = Path(__file__).resolve().parents[2]

# Keep track of background recording tasks
recording_tasks = {}
recording_flags = {}

async def _record_screen_bg(filename: str, duration_sec: int, record_id: str):
    """Background coroutine to record screen cleanly"""
    filepath = BASE_DIR / "data" / "recordings"
    filepath.mkdir(parents=True, exist_ok=True)
    full_path = filepath / filename

    try:
        with mss.mss() as sct:
            monitor = sct.monitors[1] # Primary monitor
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            # 20.0 fps
            out = cv2.VideoWriter(str(full_path), fourcc, 20.0, (monitor["width"], monitor["height"]))
            
            recording_flags[record_id] = True
            start_time = time.time()
            
            while recording_flags.get(record_id, False) and (time.time() - start_time) < duration_sec:
                img = np.array(sct.grab(monitor))
                # mss is BGRA, cv2 needs BGR
                frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                out.write(frame)
                await asyncio.sleep(0.04) # roughly 20-25fps loop yield
                
            out.release()
    except Exception as e:
        print(f"Recording error background: {e}")
    finally:
        if record_id in recording_tasks:
            del recording_tasks[record_id]
        recording_flags.pop(record_id, None)

@function_tool
async def start_video_recording(context: RunContext, duration_sec: int = 10, filename: str = "zoya_record.mp4") -> str:
    """
    Start recording the computer screen in the background without Powershell.
    It will automatically save the recording in 'd:\\ai\\data\\recordings\\'.

    Args:
        duration_sec: How many seconds to record for. Ex: 15. Default 10.
        filename: Name of the video file, must end in .mp4.
    """
    record_id = "rec_" + str(int(time.time()))
    if not filename.endswith(".mp4"):
        filename += ".mp4"
        
    task = asyncio.create_task(_record_screen_bg(filename, duration_sec, record_id))
    recording_tasks[record_id] = task
    
    path_to_save = BASE_DIR / "data" / "recordings" / filename
    return f"🎥 Background video recording shuru ho gayee hai. Yeh {duration_sec} seconds tak record karega aur '{path_to_save}' mien save kar dega."

@function_tool
async def stop_video_recording(context: RunContext) -> str:
    """
    Stop all currently running background screen video recordings immediately.
    """
    if not recording_tasks:
        return "Koi recording chaalu hi nahi hai!"
        
    for k in recording_flags.keys():
        recording_flags[k] = False
        
    return "🛑 Saari recordings foran rook di gayi hain aur save ho gai hain."
