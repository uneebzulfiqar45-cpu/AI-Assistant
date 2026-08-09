import os
import asyncio
from pathlib import Path
from zoya.os.Jarvis_window_CTRL import APP_MAPPINGS
from zoya.os.zoya_filesystem import read_text_file, write_text_file, create_folder, delete_item

async def test_file_tools():
    print("\n--- Testing File Tools ---")
    test_path = Path("D:/ai/test_file.txt")
    test_folder = Path("D:/ai/test_folder")

    # 1. Test Writing
    print("Testing write_text_file...")
    res = await write_text_file(None, str(test_path), "Zoya Feature Test: Working!")
    print(res)

    # 2. Test Reading
    print("Testing read_text_file...")
    res = await read_text_file(None, str(test_path))
    print(res)

    # 3. Test Folder Creation
    print("Testing create_folder...")
    res = await create_folder(None, str(test_folder))
    print(res)

    # 4. Test Deletion
    print("Testing delete_item...")
    res = await delete_item(None, str(test_path))
    print(res)
    res = await delete_item(None, str(test_folder))
    print(res)

def test_app_paths():
    print("\n--- Testing App Mappings ---")
    essential_apps = ["chrome", "vs code", "zoom", "word", "excel", "xampp", "steam"]
    for app in essential_apps:
        path = APP_MAPPINGS.get(app)
        if not path:
            print(f"❌ {app}: Mapping missing!")
            continue
            
        if path.startswith("http") or path.startswith("shell:") or path.startswith("ms-"):
            print(f"✅ {app}: {path} (System/Web)")
        else:
            exists = os.path.exists(path)
            status = "✅ EXISTS" if exists else "❌ NOT FOUND"
            print(f"{status} | {app}: {path}")

async def main():
    test_app_paths()
    await test_file_tools()
    print("\n--- All System Tests Passed! ---")

if __name__ == "__main__":
    asyncio.run(main())
