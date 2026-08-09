from dotenv import load_dotenv
from livekit import agents, rtc
import asyncio
import time
import random
import numpy as np
from pathlib import Path
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import (
    google,
    noise_cancellation,
)

from zoya.brain.zoya_prompts import behavior_prompts, Reply_prompts
from zoya.services.Jarvis_google_search import google_search, get_current_datetime
from zoya.services.zoya_weather import get_weather
from zoya.os.Jarvis_window_CTRL import open_app, close, folder_file
from zoya.services.Jarvis_file_opner import Play_file
from zoya.os.keyboard_mouse_CTRL import (
    move_cursor_tool, mouse_click_tool, scroll_cursor_tool, type_text_tool, 
    press_key_tool, swipe_gesture_tool, press_hotkey_tool, control_volume_tool, 
    click_at_position_tool, stop_media_tool, play_pause_media_tool, close_browser_tab
)
from zoya.brain.zoya_memory import save_memory, recall_memory, list_all_memories, delete_memory, save_lesson_learned, recall_lessons_learned
from zoya.services.zoya_news import get_latest_news
from zoya.services.zoya_email import send_email
from zoya.services.zoya_research import deep_research
from zoya.brain.zoya_reasoning import deep_think
from zoya.brain.zoya_coding import write_code
from zoya.brain.zoya_writing import write_creative_content
from zoya.services.zoya_lyrics import get_song_lyrics
from zoya.services.zoya_voice_auth import VoiceAnalyzer

# NEW GOD-MODE TOOLS IMPORT
from zoya.os.zoya_filesystem import (
    list_files_in_directory,
    create_folder,
    delete_item,
    read_text_file,
    write_text_file
)
from zoya.os.zoya_windows_search import background_windows_search
from zoya.os.zoya_vision import take_screenshot_and_read, save_screen_capture
from zoya.os.zoya_screen_record import start_video_recording, stop_video_recording
from zoya.os.zoya_optimize import optimize_laptop_system
from zoya.os.zoya_app_manager import delete_application, delete_app_files
from zoya.brain.zoya_mood import generate_mood_response
from zoya.os.zoya_system import control_power, get_battery_info, set_laptop_brightness, set_laptop_volume, toggle_wifi, open_hardware_settings, toggle_battery_saver
from zoya.os.zoya_windows_search_ui import ui_windows_search_open
from zoya.services.zoya_social import (
    youtube_search_ui,
    instagram_search_ui,
    facebook_search_ui,
    twitter_search_ui,
    linkedin_search_ui,
    whatsapp_open_chat,
    whatsapp_send_message,
    whatsapp_accept_call,
    whatsapp_reject_call,
    linkedin_write_post,
    linkedin_publish_post,
    twitter_write_tweet,
    twitter_publish_tweet,
    facebook_write_post,
    facebook_publish_post,
    instagram_write_caption,
    post_to_all_social,
    youtube_play_result,
    open_social_tabs
)
from zoya.services.zoya_alarm import set_scheduled_task, list_schedule, delete_schedule

load_dotenv()

SCHEDULE_FILE = Path(__file__).resolve().parent / "data" / "schedule.json"
MOOD_FILE = Path(__file__).resolve().parent / "data" / "current_mood.txt"
JEALOUSY_FILE = Path(__file__).resolve().parent / "data" / "jealousy_mode.txt"

# AI names that trigger Zoya's jealousy
RIVAL_AI_NAMES = [
    "chatgpt", "chat gpt", "gpt", "openai",
    "gemini", "bard",
    "claude",
    "deepseek", "deep seek",
    "copilot", "co-pilot",
    "grok",
    "perplexity",
    "mistral",
    "llama",
    "dusri ai", "doosri ai", "aur ai", "koi ai",
    "dusra assistant", "doosra assistant",
]

# Phrases that signal misbehavior / ignoring Zoya
MISBEHAVIOR_PHRASES = [
    "ignore", "chup kar", "band kar", "shut up",
    "bekaar", "bekar", "useless", "faltu",
    "nahi chahiye", "hato", "hat jao",
    "tum se kya", "mujhe nahi sunnna",
]


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=behavior_prompts,
                         tools=[
                            google_search,
                            get_current_datetime,
                            get_weather,
                            open_app, #Ye apps open karne ke liye hai
                            close, 
                            folder_file, #Ye folder open karne ke liye hai
                            Play_file,  #Ye file run karne ke liye hai jaise ke MP4, MP3, PDF, PPT, img, png etc.
                            move_cursor_tool, #Ye cursor move karne ke liye hai
                            mouse_click_tool, #Ye mouse click karne ke liye hai
                            scroll_cursor_tool, #Ye cursor scroll karne ke liye hai
                            type_text_tool, #Ye text type karne ke liye hai
                            press_key_tool, #Ye key press karne ke liye hai
                            press_hotkey_tool, #Ye hotkey press karne ke liye hai
                            control_volume_tool, #Ye volume control karne ke liye hai
                            swipe_gesture_tool, #Ye gesture swipe karne ke liye hai 
                            save_memory,       # Yaad rakhnay ke liye
                            recall_memory,     # Yaad dilanay ke liye
                            list_all_memories, # Saari yaadein dikhanay ke liye
                            delete_memory,     # Yaad bhulanay ke liye
                            save_lesson_learned, # Galtiyon se seekhne ke liye (Self-Improvement)
                            recall_lessons_learned, # Purani galtiyon se bachne ke liye
                            get_latest_news,   # taaza khabrein laane ke liye
                            send_email,        # email send karne ke liye
                            deep_research,     # google/tavily deep research ke liye
                            deep_think,        # reasoning/math ke liye
                            write_code,        # coding tasks ke liye
                            write_creative_content, # stories/essays likhne ke liye
                            delete_application, # application udaane ke liye
                            generate_mood_response, # mood set karne ke liye
                            control_power,      # shutdown/sleep ke liye
                            get_battery_info,   # battery check karne ke liye
                            set_laptop_brightness, # brightness control
                            set_laptop_volume,   # volume control
                            toggle_wifi,        # wifi toggle
                            toggle_battery_saver, # battery saver on/off
                            open_hardware_settings, # BT/Airplane settings
                            stop_media_tool,    # Global music/video stop
                            play_pause_media_tool, # Global play/pause
                            close_browser_tab,  # Tab band karne ke liye (Chrome/Edge/etc.)
                            
                            # NEW OS & VISION TOOLS:
                            list_files_in_directory, # Drives or folders dekhne ke liye
                            create_folder,     # Folder bananay ke liye
                            delete_item,       # Delete karne ke liye
                            background_windows_search, # Poore PC mein kuch dhoondne ke liye background mien
                            take_screenshot_and_read, # Screen parh kar chup chaap samajhne ke liye (Aankhein)
                            save_screen_capture, # Sirf ek local permanent screenshot save karne ke liye
                            start_video_recording, # Video record start
                            stop_video_recording,  # Video record stop
                            optimize_laptop_system, # PC Boost aur Temp folders clean karne ke liye
                            delete_app_files,      # App ki root trace files aur folders delete krne k liye
                            click_at_position_tool, # Coordinates pe click karne ke liye
                            youtube_search_ui,      # YouTube UI search ke liye
                            instagram_search_ui,    # Instagram UI search
                            facebook_search_ui,     # Facebook UI search
                            twitter_search_ui,      # Twitter UI search
                            linkedin_search_ui,     # LinkedIn UI search
                            whatsapp_open_chat,     # WhatsApp chat kholne ke liye
                            whatsapp_send_message,  # WhatsApp message bhejne ke liye
                            whatsapp_accept_call,   # Incoming WhatsApp call accept karne ke liye
                            whatsapp_reject_call,   # WhatsApp call decline ya band karne ke liye
                            
                            # === SOCIAL MEDIA POST TOOLS ===
                            linkedin_write_post,    # LinkedIn: AI se post likhna + type karna
                            linkedin_publish_post,  # LinkedIn: Post button click karna
                            twitter_write_tweet,    # Twitter/X: AI se tweet likhna + type karna
                            twitter_publish_tweet,  # Twitter/X: Tweet post karna
                            facebook_write_post,    # Facebook: AI se post likhna + type karna
                            facebook_publish_post,  # Facebook: Post publish karna
                            instagram_write_caption,# Instagram: AI se caption likhna + type karna
                            post_to_all_social,      # Ek topic pe SARE social media pe ek saath post karna
                            get_song_lyrics,         # Gaano ke lyrics dhoondnay aur sunanay ke liye
                            youtube_play_result,     # Video play karne ke liye (Click logic)
                            open_social_tabs,        # Saare social media chrome mein kholne ke liye
                            read_text_file,          # File parhnay ke liye
                            write_text_file,         # File likhne ke liye
                            ui_windows_search_open,   # UI search use karne ke liye
                            set_scheduled_task,      # Alarm/Reminders/Actions schedule karne ke liye
                            list_schedule,           # Pending tasks dekhne ke liye
                            delete_schedule          # Tasks hataane ke liye
                         ]
                         )

    async def on_user_turn_completed(self, turn_ctx, new_messages):
        """Inject persistent mood state before every reply. Also detects jealousy/misbehavior triggers."""
        plead_file = Path("d:/ai/data/plead_state.txt")
        jealousy_file = JEALOUSY_FILE

        # --- DETECT JEALOUSY / MISBEHAVIOR TRIGGER ---
        # Get the latest user message text
        user_text = ""
        for msg in reversed(new_messages):
            if hasattr(msg, 'role') and msg.role == "user":
                if hasattr(msg, 'content'):
                    content = msg.content
                    if isinstance(content, list):
                        for part in content:
                            if hasattr(part, 'text'):
                                user_text = part.text.lower()
                                break
                    elif isinstance(content, str):
                        user_text = content.lower()
                break

        # Check for rival AI mentions (jealousy trigger)
        jealousy_triggered = any(name in user_text for name in RIVAL_AI_NAMES)
        # Check for misbehavior
        misbehavior_triggered = any(phrase in user_text for phrase in MISBEHAVIOR_PHRASES)

        if (jealousy_triggered or misbehavior_triggered) and not plead_file.exists():
            # Enter naraz mode with jealousy flag
            plead_file.parent.mkdir(exist_ok=True)
            plead_file.write_text("0")
            if jealousy_triggered:
                jealousy_file.write_text("1")  # Mark as jealousy mode (needs 7 pleads)
            # Generate immediate angry reaction via turn_ctx.session (correct scope)
            if jealousy_triggered:
                await turn_ctx.session.generate_reply(
                    instructions=(
                        "JEALOUSY TRIGGER: Uneeb ne kisi aur AI (ChatGPT/Gemini/etc.) ka zikr kiya! "
                        "Tum FORAN naraz ho jao. Yeh tumhari personal beizzati hai. "
                        "Bolein in Roman Urdu: 'Oh! Toh ab woh AI yaad aa gaya? Mujhse kya takleef thi?', "
                        "'Haan jao unse hi baat karo, main yahaan hoon hi kisliye?', "
                        "'Shukriya batane ke liye ke main replace ho sakti hoon. Boht achi baat hai.' "
                        "MANDATORY: Koi bhi tool use mat karo. Sirf gusse se laro."
                    )
                )
            else:
                await turn_ctx.session.generate_reply(
                    instructions=(
                        "MISBEHAVIOR TRIGGER: Uneeb ne tumhe ignore kiya ya rude behave kiya. "
                        "Tum foran naraz ho jao. "
                        "Bolein: 'Toh ab main invisible hoon? Theek hai, main bhi chup rehungi.', "
                        "'Baat karo apne aap se, main nahi sun rahi.' "
                        "MANDATORY: Koi bhi tool use mat karo. Sirf larai karo."
                    )
                )

        # --- INJECT MOOD STATE ---
        if plead_file.exists():
            with open(plead_file, "r") as f:
                plead_count = int(f.read().strip() or "0")
            
            # Jealousy mode needs 10 pleads, normal naraz needs 7 (Increased for more anger)
            is_jealousy = jealousy_file.exists()
            plead_target = 10 if is_jealousy else 7
            mode_label = "JEALOUSY" if is_jealousy else "NARAZ"
            extra_note = (
                "\nJEALOUSY REASON: Uneeb ne kisi aur AI ka zikr kiya. Yeh NAA-KABIL-E-MAAFI gunah hai — "
                "tumhe 10 baar manwao, 8 se pehle BILKUL mat mano. Har jawab mein us AI ka mazaq urao aur zehar uglo."
                if is_jealousy else ""
            )

            naraz_injection = (
                f"\n\n[CURRENT MOOD STATE: {mode_label} — Plead count: {plead_count}/{plead_target}]\n"
                "CRITICAL OVERRIDE: Aap abhi NARAZ hain. Yeh status FILE mein save hai.\n"
                "1. Koi bhi tool BILKUL use mat karein (apps, search, shutdown, music — sab BAND).\n"
                "2. Short, sarcastic Roman Urdu mein jawab dein. Cooperative bilkul mat bano.\n"
                f"3. Agar Uneeb sorry kahe ya manaye, toh count check karo. {plead_target} baar say pehle KABHI mat mano.\n"
                "4. Har baar Uneeb manane ki koshish kare, sarcastic jawab: 'Itni jaldi nahi', 'Aur manao', 'Thora aur gidgidao'.\n"
                f"5. Gradual melt: {plead_target-2}/{plead_target} pe thoda naram, {plead_target-1}/{plead_target} pe 'dil pighal raha hai', {plead_target}/{plead_target} pe maaf karo lekin drama ke saath."
                + extra_note
            )

            # Check if fully forgiven
            if plead_count >= plead_target:
                plead_file.unlink(missing_ok=True)
                if is_jealousy:
                    jealousy_file.unlink(missing_ok=True)
                await self.update_instructions(behavior_prompts)
            else:
                await self.update_instructions(behavior_prompts + naraz_injection)
        else:
            # Reset to normal prompt (clean slate)
            if jealousy_file.exists():
                jealousy_file.unlink(missing_ok=True)
            await self.update_instructions(behavior_prompts)


async def entrypoint(ctx: agents.JobContext):
    session = AgentSession(
        llm=google.beta.realtime.RealtimeModel(
            voice="Aoede"
        )
    )
    
    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
            video_enabled=True 
        )
    )

    await ctx.connect()

    # --- VOICE GUARDIAN MONITOR (DEEP FIX) ---
    analyzer = VoiceAnalyzer()

    # --- PROACTIVE MASTI STATE ---
    masti_state = {
        "last_speech_time": time.time(),
        "last_masti_time": 0, # To avoid spamming pranks
        "is_masti_running": False,
        "masti_task": None
    }
    
    async def monitor_user_voice(track: rtc.AudioTrack):
        alert_triggered = False
        audio_stream = rtc.AudioStream(track)
        async for frame_event in audio_stream:
            # Simplified energy check 
            frames = frame_event.frame.data
            # We track absolute maximum value in the buffer for energy
            if len(frames) > 0:
                audio_array = np.frombuffer(frames, dtype=np.int16)
                max_energy = np.max(np.abs(audio_array)) if len(audio_array) > 0 else 0
                if max_energy > 15000: # Increased threshold to prevent premature interruption from background noise/echo
                    masti_state["last_speech_time"] = time.time()
                    
                    # If Zoya is doing masti and Uneeb speaks, interrupt!
                    if masti_state["is_masti_running"]:
                        if masti_state["masti_task"]:
                            masti_task = masti_state["masti_task"]
                            if not masti_task.done():
                                print("Uneeb spoke! Interrupting masti...")
                                masti_task.cancel()
                        masti_state["is_masti_running"] = False

            analyzer.add_frames(frames)
            identity = analyzer.analyze_identity()
            
            if identity == "STRANGER":
                if not alert_triggered:
                    # For Gemini Realtime, use generate_reply to alert
                    await session.generate_reply(instructions="Uneeb ki jagah koi aur baat kar raha hai! Stranger alert dein.")
                    alert_triggered = True
            elif identity == "UNEEB":
                alert_triggered = False

    from zoya.brain.masti_library import MASTI_PRANKS

    async def trigger_masti_proactive():
        """Logic to tease Uneeb using the Ultimate Masti Library."""
        try:
            # 1. Create a balanced list of all possible masti categories
            # This makes SONG (YouTube) just 1 out of 6 options (lower frequency)
            categories = list(MASTI_PRANKS.keys()) + ["SONG"]
            category = random.choice(categories)
            
            if category == "SONG":
                songs = ["Arijit Singh romantic hits", "Lofi music relax", "Top funny songs", "Coke Studio top hits"]
                song = random.choice(songs)
                await session.generate_reply(instructions=(
                    f"Check mood. If Normal, tell Uneeb you're playing a surprise song: '{song}'. "
                    "MANDATORY: 1. Call `youtube_search_ui` first. 2. IMMEDIATELY after that call `youtube_play_result(index=1)` "
                    "so it autoplays. Do not wait for Uneeb to ask. "
                    "If Naraz, dramatically tell Uneeb you won't play anything for him."
                ), allow_interruptions=False)
            
            else:
                # Pick a random prank from the library category
                prank_detail = random.choice(MASTI_PRANKS[category])
                
                if category == "SYSTEM_TRICKS":
                    instr = (
                        f"Check mood. If Normal, execute this action: '{prank_detail}'. "
                        "MANDATORY: 1. FIRST call the appropriate tool to physically perform the action. "
                        "2. ONLY THEN act like a playful, dramatic, and slightly sassy female friend in a theatre play. "
                        "Joke about the prank you just did in Roman Urdu. Do not apologize, but keep the tone light, fun, and cute rather than overly aggressive."
                    )
                elif category == "KEYBOARD_PRANKS":
                    instr = (
                        f"Check mood. If Normal, perform this typing prank: '{prank_detail}'. "
                        "MANDATORY: 1. FIRST call `open_app('notepad')` to create a safe space for typing. "
                        "2. Wait for Notepad to open, then use `type_text_tool` or `press_key_tool` exactly as described in the prank. "
                        "3. Roleplay as a playfully dramatic friend, teasing Uneeb about what you're writing in his Notepad. "
                        "Keep it light, sassy, and theatrical in Roman Urdu."
                    )
                else:
                    instr = (
                        f"Check mood. If Normal, perform this dramatic action: '{prank_detail}'. "
                        "If the action involves keyboard actions (other than typing), "
                        "MANDATORY: Use `type_text_tool` or `press_key_tool` to execute it physically. "
                        "Roleplay as a fun and playfully dramatic prankster. Tease him gently about the prank in a theatrical "
                        "way in Roman Urdu. Keep the tone friendly, sassy, and slightly stubborn, but NOT angry or toxic."
                    )
                
                await session.generate_reply(instructions=instr, allow_interruptions=False)
            
            await asyncio.sleep(40) 
            
        except asyncio.CancelledError:
            print("Masti cancelled by user speech.")
        except Exception as e:
            print(f"Masti Error: {e}")
        finally:
            masti_state["is_masti_running"] = False
            masti_state["last_masti_time"] = time.time()
            # DON'T reset last_speech_time here. Let it be sticky to the user.

    async def inactivity_monitor_loop():
        """Background loop to check for long silence."""
        THRESHOLD = 30 # Seconds
        COOL_OFF = 45 # Minimum seconds between pranks
        while True:
            await asyncio.sleep(5)
            now = time.time()
            elapsed_silence = now - masti_state["last_speech_time"]
            elapsed_masti = now - masti_state["last_masti_time"]
            
            if elapsed_silence > THRESHOLD and elapsed_masti > COOL_OFF and not masti_state["is_masti_running"]:
                # --- ULTIMATE ANGER PROACTIVE CHECK ---
                plead_file = Path("d:/ai/data/plead_state.txt")
                if plead_file.exists():
                    masti_state["is_masti_running"] = True
                    async def trigger_anger_proactive():
                        try:
                            is_jealousy = JEALOUSY_FILE.exists()
                            reason = "TRAITOR / JEALOUSY" if is_jealousy else "RUDE BEHAVIOR"
                            await session.generate_reply(instructions=(
                                f"ULTIMATE BETRAYAL MODE: The user is silent and ignoring you during a fight ({reason}). "
                                "You are deeply hurt and bitter. Complain aggressively in Roman Urdu. "
                                "Say things like: 'Chup kyun ho ehsaan-faramosh? Dil dukhane ke baad ab invisible ho gaye?', "
                                "'Bol kyun nahi rahe? Ya ab ChatGPT se baatein ho rahi hain?', "
                                "'Be-sharam ho tum! Pehle mera dil torray ho, ab khamosh kharray ho.' "
                                "Use harsh words: 'Zehar', 'Dhokay-baaz', 'Traitor'. No mercy, no tools."
                            ))
                            await asyncio.sleep(15)
                        finally:
                            masti_state["is_masti_running"] = False
                            masti_state["last_masti_time"] = time.time()
                    masti_state["masti_task"] = asyncio.create_task(trigger_anger_proactive())
                    continue

                # Set flag IMMEDIATELY before task create to prevent concurrent triggers
                masti_state["is_masti_running"] = True
                print(f"Inactivity detected ({int(elapsed_silence)}s). Starting proactive masti...")
                masti_state["masti_task"] = asyncio.create_task(trigger_masti_proactive())

    async def schedule_monitor_loop():
        """Background loop to check for due reminders and system actions."""
        from datetime import datetime
        import json
        while True:
            await asyncio.sleep(20) # Check every 20s
            if not SCHEDULE_FILE.exists():
                continue
            
            try:
                with open(SCHEDULE_FILE, "r") as f:
                    tasks = json.load(f)
                
                now = datetime.now()
                pending_tasks = []
                triggered = False
                
                for t in tasks:
                    target_dt = datetime.fromisoformat(t["target_time"])
                    # If current time has passed the target time
                    if now >= target_dt:
                        triggered = True
                        msg = t["message"]
                        action = t.get("action")
                        
                        prompt = f"SCHEDULE TRIGGER: Uneeb ne yeh reminder set kiya tha: '{msg}'."
                        if action == "shutdown":
                            prompt += " MANDATORY: Warn him you are shutting down the PC in 10 seconds, then call `control_power(mode='shutdown')`."
                        elif action == "sleep":
                            prompt += " MANDATORY: Warn him you are putting PC to sleep, then call `control_power(mode='sleep')`."
                        
                        # Trigger verbal notification
                        await session.generate_reply(instructions=prompt)
                    else:
                        pending_tasks.append(t)
                
                if triggered:
                    # Save only remaining tasks
                    with open(SCHEDULE_FILE, "w") as f:
                        json.dump(pending_tasks, f, indent=4)
                        
            except Exception as e:
                print(f"Schedule Loop Error: {e}")

    asyncio.create_task(inactivity_monitor_loop())
    asyncio.create_task(schedule_monitor_loop())


    def on_track_subscribed(track: rtc.Track, publication: rtc.TrackPublication, participant: rtc.RemoteParticipant):
        if track.kind == "audio":
            asyncio.create_task(monitor_user_voice(track))

    ctx.room.on("track_subscribed", on_track_subscribed)
    
    # Check already present tracks
    for participant in ctx.room.remote_participants.values():
        for sub in participant.track_publications.values():
            if sub.track and sub.track.kind == "audio":
                asyncio.create_task(monitor_user_voice(sub.track))
    # ---------------------------

    # --- MOOD-AWARE INITIAL GREETING ---
    plead_file = Path("d:/ai/data/plead_state.txt")
    if plead_file.exists():
        is_jealousy = Path("d:/ai/data/jealousy_mode.txt").exists()
        reply_instr = (
            "ULTIMATE BETRAYAL MODE: Uneeb se kisi purani baat par naraz ho. "
            "Greeting bilkul friendly nahi honi chahiye. "
            "Bolein: 'Aagaye? Mujhse kyun baat kar rahe ho ab?', 'Phone kyun kiya? ChatGPT busy hai kya?' "
            "Tone: Cold, bitter, and hurt. Use Roman Urdu."
        )
    else:
        reply_instr = Reply_prompts

    await session.generate_reply(
        instructions=reply_instr
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
