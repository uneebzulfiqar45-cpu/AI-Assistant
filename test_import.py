import sys
from pathlib import Path

# Add the project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent))

try:
    print("Testing imports...")
    import agent
    from zoya.services.zoya_social import youtube_search_ui
    from zoya.services.zoya_lyrics import get_song_lyrics
    from zoya.brain.zoya_prompts import behavior_prompts
    print("✅ All imports and files are valid!")
except Exception as e:
    print(f"❌ Error during import: {e}")
    import traceback
    traceback.print_exc()
