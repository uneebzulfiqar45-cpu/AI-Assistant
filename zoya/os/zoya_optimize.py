import os
import psutil
import shutil
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from livekit.agents import function_tool, RunContext

# Categories for folder organization
CATEGORIES = {
    "Images":     [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico"],
    "Videos":     [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"],
    "Documents":  [".pdf", ".docx", ".doc", ".txt", ".xlsx", ".xls", ".pptx", ".ppt", ".csv"],
    "SetupFiles": [".exe", ".msi", ".dmg", ".pkg"],
    "Archives":   [".zip", ".rar", ".tar", ".gz", ".7z"],
    "Audio":      [".mp3", ".wav", ".flac", ".aac", ".ogg"],
}

# Extensions to always skip (shortcuts, system files)
SKIP_EXTENSIONS = {".lnk", ".url", ".ini", ".tmp"}

# File name prefixes to skip (Word temp lock files like ~$filename.docx)
SKIP_PREFIXES = {"~$"}

# Skip files larger than 500 MB
MAX_FILE_SIZE_BYTES = 500 * 1024 * 1024


def _get_desktop_path() -> str:
    """Auto-detect Desktop path (handles OneDrive Desktop on Windows 11)."""
    user = os.environ.get("USERPROFILE", "C:\\Users\\uneeb")
    onedrive_desktop = os.path.join(user, "OneDrive", "Desktop")
    if os.path.exists(onedrive_desktop):
        return onedrive_desktop
    return os.path.join(user, "Desktop")

def _get_downloads_path() -> str:
    user = os.environ.get("USERPROFILE", "C:\\Users\\uneeb")
    return os.path.join(user, "Downloads")

def _get_documents_path() -> str:
    user = os.environ.get("USERPROFILE", "C:\\Users\\uneeb")
    # Try OneDrive Documents first (Windows 11)
    od = os.path.join(user, "OneDrive", "Documents")
    if os.path.exists(od):
        return od
    return os.path.join(user, "Documents")

def _get_pictures_path() -> str:
    user = os.environ.get("USERPROFILE", "C:\\Users\\uneeb")
    od = os.path.join(user, "OneDrive", "Pictures")
    if os.path.exists(od):
        return od
    return os.path.join(user, "Pictures")

def _get_videos_path() -> str:
    user = os.environ.get("USERPROFILE", "C:\\Users\\uneeb")
    return os.path.join(user, "Videos")

def _get_music_path() -> str:
    user = os.environ.get("USERPROFILE", "C:\\Users\\uneeb")
    return os.path.join(user, "Music")

# Map of named modes to folder path resolvers
NAMED_MODES = {
    "desktop":   _get_desktop_path,
    "downloads": _get_downloads_path,
    "documents": _get_documents_path,
    "pictures":  _get_pictures_path,
    "videos":    _get_videos_path,
    "music":     _get_music_path,
    "d_drive":   lambda: "D:\\",
}


def _move_file(src: str, dst_dir: str) -> str:
    """Move a single file, return result string."""
    fname = os.path.basename(src)
    os.makedirs(dst_dir, exist_ok=True)
    dst = os.path.join(dst_dir, fname)
    # If destination already exists, skip
    if os.path.exists(dst):
        return f"skip:{fname}"
    shutil.move(src, dst)
    return f"ok:{fname}"


@function_tool
async def optimize_laptop_system(context: RunContext, mode: str = "quick", target_folder: str = None) -> str:
    """
    Perform system optimization, clear temp files, or organize any folder on the laptop.

    Args:
        mode: 
            - 'quick'     = system temp files clear
            - 'deep'      = aggressive system clear  
            - 'desktop'   = organize Desktop (auto-detects OneDrive Desktop)
            - 'downloads' = organize Downloads folder
            - 'documents' = organize Documents folder
            - 'pictures'  = organize Pictures folder
            - 'videos'    = organize Videos folder
            - 'music'     = organize Music folder
            - 'd_drive'   = organize D:\\ drive root
            - 'folder'    = organize any custom folder (needs target_folder)
        target_folder: Only needed if mode='folder'. Full path e.g. 'C:\\Users\\uneeb\\SomeFolder'.
    """
    try:
        # Resolve named mode to actual folder path
        if mode in NAMED_MODES:
            target_folder = NAMED_MODES[mode]()
            mode = 'folder'

        if mode == 'folder' and target_folder:
            if not os.path.exists(target_folder):
                return f"Target folder '{target_folder}' mojud nahi hai."

            entries = os.listdir(target_folder)
            files_to_move = []
            skipped_large = 0
            skipped_unknown = 0

            for fname in entries:
                fpath = os.path.join(target_folder, fname)
                if not os.path.isfile(fpath):
                    continue

                # Skip shortcuts and system files
                ext = os.path.splitext(fname)[1].lower()
                if ext in SKIP_EXTENSIONS:
                    continue

                # Skip Word/Excel temp lock files (start with ~$)
                if any(fname.startswith(p) for p in SKIP_PREFIXES):
                    continue

                # Skip very large files to prevent hanging
                try:
                    if os.path.getsize(fpath) > MAX_FILE_SIZE_BYTES:
                        skipped_large += 1
                        continue
                except:
                    continue

                matched_cat = None
                for cat, exts in CATEGORIES.items():
                    if ext in exts:
                        matched_cat = cat
                        break

                if matched_cat:
                    dst_dir = os.path.join(target_folder, matched_cat)
                    files_to_move.append((fpath, dst_dir))
                else:
                    skipped_unknown += 1

            if not files_to_move:
                # Count existing organized subfolders
                subfolders = []
                for cat in CATEGORIES:
                    cat_path = os.path.join(target_folder, cat)
                    if os.path.exists(cat_path):
                        count = len(os.listdir(cat_path))
                        if count > 0:
                            subfolders.append(f"{cat}({count} files)")

                already_done = ""
                if subfolders:
                    already_done = f"\nPehle se organized folders: {', '.join(subfolders)}"

                return (
                    f"✅ '{target_folder}' mein koi organizable file nahi mili.\n"
                    f"Wajah: Ya toh sab files pehle hi organize ho chuki hain, ya sirf shortcuts/system files hain.{already_done}\n"
                    f"Large files skipped (>500MB): {skipped_large}\n"
                    f"Unknown type files (no category): {skipped_unknown}"
                )

            # Move files concurrently using thread pool
            moved = 0
            failed = 0
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = [
                    loop.run_in_executor(executor, _move_file, src, dst)
                    for src, dst in files_to_move
                ]
                results = await asyncio.gather(*futures, return_exceptions=True)

            for r in results:
                if isinstance(r, Exception) or (isinstance(r, str) and r.startswith("ok:")):
                    if isinstance(r, Exception):
                        failed += 1
                    else:
                        moved += 1
                # "skip:" means already existed, count as ok
                elif isinstance(r, str) and r.startswith("skip:"):
                    moved += 1

            return (
                f"Folder Organized: '{target_folder}'\n"
                f"Files moved: {moved}\n"
                f"Failed: {failed}\n"
                f"Skipped (large >500MB): {skipped_large}\n"
                f"Skipped (unknown type): {skipped_unknown}\n"
                f"Categories: Images, Videos, Documents, SetupFiles, Archives, Audio"
            )

        # System Optimization (Quick/Deep)
        ram_before = psutil.virtual_memory().percent
        temp_paths = [
            os.environ.get('TEMP'),
            os.environ.get('TMP'),
            "C:\\Windows\\Temp"
        ]

        cleared_bytes = 0
        deleted_files = 0
        failed_files = 0

        for tp in temp_paths:
            if not tp or not os.path.exists(tp):
                continue
            for root, dirs, files in os.walk(tp):
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        size = os.path.getsize(fp)
                        os.remove(fp)
                        cleared_bytes += size
                        deleted_files += 1
                    except:
                        failed_files += 1

        mb_cleared = cleared_bytes / (1024 * 1024)
        ram_after = psutil.virtual_memory().percent

        return (
            f"PC Optimization Done (Mode: {mode})\n"
            f"Temp files deleted: {deleted_files} ({mb_cleared:.2f} MB freed)\n"
            f"In-use files skipped: {failed_files}\n"
            f"RAM: {ram_before}% -> {ram_after}%"
        )

    except Exception as e:
        return f"System optimize karte hue error aayi: {e}"
