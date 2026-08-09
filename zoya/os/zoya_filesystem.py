import os
from pathlib import Path
from livekit.agents import function_tool, RunContext

@function_tool
async def list_files_in_directory(context: RunContext, path: str = None) -> str:
    """
    List all the folders and files in any directory on the PC.
    If no path is provided, it lists the drives available.

    Args:
        path: Absolute path to the folder to list (e.g., 'C:\\', 'd:\\ai')
    """
    if path is None:
        # Simple windows drive detection roughly
        drives = [f"{d}:\\" for d in "CDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(f"{d}:\\")]
        return f"Aap ne path nahi diya. Available drives yeh hain: {', '.join(drives)}"

    try:
        entries = os.listdir(path)
        folders = [e for e in entries if os.path.isdir(os.path.join(path, e))]
        files = [e for e in entries if os.path.isfile(os.path.join(path, e))]
        
        folders_str = ', '.join(folders[:20]) + ('...' if len(folders) > 20 else '')
        files_str = ', '.join(files[:20]) + ('...' if len(files) > 20 else '')
        
        return f"Path '{path}' mein:\nFolders: {folders_str}\nFiles: {files_str}"
    except Exception as e:
        return f"File system list error: {e}"

@function_tool
async def create_folder(context: RunContext, path: str) -> str:
    """
    Create a new folder exactly at the specified absolute path.

    Args:
        path: Absolute path of new folder (e.g. 'd:\\ai\\newfolder')
    """
    try:
        os.makedirs(path, exist_ok=True)
        return f"✅ '{path}' ban gaya hai."
    except Exception as e:
        return f"❌ Folder bananay mein error: {e}"

@function_tool
async def delete_item(context: RunContext, path: str) -> str:
    """
    Delete a file or folder permanently. Works even on Access Denied / locked / system-protected folders.
    Can delete anything on the PC including Desktop folders like iPhone, iCloud, iTunes backups etc.

    Args:
        path: Absolute path of file or folder to delete (e.g. 'C:\\Users\\uneeb\\Desktop\\iPhone')
    """
    import shutil
    import subprocess
    
    p = Path(path)
    if not p.exists():
        return f"❌ '{path}' mojud hi nahi hai."
    
    # Step 1: Try Python shutil (fast path)
    try:
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()
        return f"🗑️ '{path}' delete ho gaya!"
    except Exception:
        pass
    
    # Step 2: Take ownership first (fixes Access Denied), then force delete
    try:
        # Take ownership of folder and all contents
        subprocess.run(
            ["takeown", "/f", path, "/r", "/d", "y"],
            capture_output=True, text=True, timeout=30
        )
        # Grant full access to current user
        subprocess.run(
            ["icacls", path, "/grant", "Everyone:F", "/t", "/c", "/q"],
            capture_output=True, text=True, timeout=30
        )
        # Now force delete with PowerShell
        if p.is_dir():
            cmd = ["powershell", "-Command", f'Remove-Item -Path "{path}" -Recurse -Force -ErrorAction Stop']
        else:
            cmd = ["powershell", "-Command", f'Remove-Item -Path "{path}" -Force -ErrorAction Stop']
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if not p.exists():
            return f"🗑️ '{path}' delete ho gaya! (ownership le ke delete kiya)"
        
        # Last resort: cmd rmdir
        subprocess.run(["cmd", "/c", "rmdir", "/s", "/q", path], capture_output=True, timeout=15)
        if not p.exists():
            return f"🗑️ '{path}' delete ho gaya!"
        
        err = result.stderr.strip() or "Access denied — folder kisi process ne lock kiya hua hai."
        return f"❌ Delete nahi hua: {err}"
    except Exception as e:
        return f"❌ Delete karne mein error: {e}"

@function_tool
async def read_text_file(context: RunContext, path: str) -> str:
    """
    Read the content of a text-based file (txt, md, py, js, html, log etc).
    """
    try:
        p = Path(path)
        if not p.exists():
            return f"❌ File '{path}' nahi mili."
        
        # Check file size (don't read massive files)
        if p.stat().st_size > 500 * 1024:
            return "❌ File bohat bari hai (500KB se zyada). Sirf choti files parh sakti hoon."

        with open(p, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(5000) # Limit to 5000 characters for LLM context
        
        return f"📄 File content:\n---\n{content}\n---"
    except Exception as e:
        return f"❌ Parhnay mein error: {e}"

@function_tool
async def write_text_file(context: RunContext, path: str, content: str) -> str:
    """
    Create a new file or overwrite an existing one with text content.
    """
    try:
        p = Path(path)
        # Create directories if don't exist
        p.parent.mkdir(parents=True, exist_ok=True)
        
        with open(p, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return f"✅ File '{path}' pe likh di gayi hai."
    except Exception as e:
        return f"❌ Likhne mein error: {e}"
