content = open('zoya/os/Jarvis_window_CTRL.py', 'r', encoding='utf-8').read()

# Find and replace the APP_MAPPINGS block
start_marker = "# App command map"
end_marker = "}\r\n\r\n# -------------------------"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker) + len("}\r\n")

if start_idx == -1 or end_idx == -1:
    print("Markers not found!")
    print(repr(content[800:1300]))
else:
    new_block = (
        "# App command map \u2014 verified paths from actual system scan\r\n"
        "# Store apps: shell:AppsFolder\\AppID | Regular apps: full .exe path | URLs: https://...\r\n"
        "APP_MAPPINGS = {\r\n"
        "    # === System Tools ===\r\n"
        "    \"notepad\":        \"shell:AppsFolder\\\\Microsoft.WindowsNotepad_8wekyb3d8bbwe!App\",\r\n"
        "    \"calculator\":     \"calc\",\r\n"
        "    \"paint\":          \"mspaint\",\r\n"
        "    \"control panel\":  \"control\",\r\n"
        "    \"settings\":       \"ms-settings:\",\r\n"
        "    \"task manager\":   \"taskmgr\",\r\n"
        "    \"command prompt\": \"cmd\",\r\n"
        "    \"powershell\":     \"powershell\",\r\n"
        "    \"terminal\":       \"shell:AppsFolder\\\\Microsoft.WindowsTerminal_8wekyb3d8bbwe!App\",\r\n"
        "    \"snipping tool\":  \"shell:AppsFolder\\\\Microsoft.ScreenSketch_8wekyb3d8bbwe!App\",\r\n"
        "    \"sticky notes\":   \"shell:AppsFolder\\\\Microsoft.MicrosoftStickyNotes_8wekyb3d8bbwe!App\",\r\n"
        "\r\n"
        "    # === Browsers ===\r\n"
        "    \"chrome\":         \"C:\\\\Program Files\\\\Google\\\\Chrome\\\\Application\\\\chrome.exe\",\r\n"
        "    \"edge\":           \"shell:AppsFolder\\\\MSEdge\",\r\n"
        "\r\n"
        "    # === Microsoft Office ===\r\n"
        "    \"word\":           \"shell:AppsFolder\\\\Microsoft.Office.WINWORD.EXE.15\",\r\n"
        "    \"excel\":          \"shell:AppsFolder\\\\Microsoft.Office.EXCEL.EXE.15\",\r\n"
        "    \"powerpoint\":     \"shell:AppsFolder\\\\Microsoft.Office.POWERPNT.EXE.15\",\r\n"
        "    \"outlook\":        \"shell:AppsFolder\\\\Microsoft.OutlookForWindows_8wekyb3d8bbwe!Microsoft.OutlookforWindows\",\r\n"
        "\r\n"
        "    # === Communication ===\r\n"
        "    \"whatsapp\":       \"shell:AppsFolder\\\\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App\",\r\n"
        "    \"teams\":          \"shell:AppsFolder\\\\MSTeams_8wekyb3d8bbwe!MSTeams\",\r\n"
        "    \"zoom\":           \"C:\\\\Users\\\\uneeb\\\\AppData\\\\Roaming\\\\Zoom\\\\bin\\\\Zoom.exe\",\r\n"
        "\r\n"
        "    # === Social / Web ===\r\n"
        "    \"youtube\":        \"https://www.youtube.com\",\r\n"
        "    \"facebook\":       \"https://www.facebook.com\",\r\n"
        "    \"instagram\":      \"https://www.instagram.com\",\r\n"
        "    \"twitter\":        \"https://x.com\",\r\n"
        "    \"linkedin\":       \"https://www.linkedin.com\",\r\n"
        "    \"github\":         \"https://github.com\",\r\n"
        "\r\n"
        "    # === Dev Tools ===\r\n"
        "    \"vs code\":        \"shell:AppsFolder\\\\Microsoft.VisualStudioCode\",\r\n"
        "    \"vscode\":         \"shell:AppsFolder\\\\Microsoft.VisualStudioCode\",\r\n"
        "    \"github desktop\": \"shell:AppsFolder\\\\com.squirrel.GitHubDesktop.GitHubDesktop\",\r\n"
        "    \"xampp\":          \"D:\\\\xamp\\\\xampp-control.exe\",\r\n"
        "\r\n"
        "    # === Media & Entertainment ===\r\n"
        "    \"vlc\":            \"C:\\\\Program Files\\\\VideoLAN\\\\VLC\\\\vlc.exe\",\r\n"
        "    \"steam\":          \"D:\\\\steam\\\\Steam.exe\",\r\n"
        "    \"xbox\":           \"shell:AppsFolder\\\\Microsoft.GamingApp_8wekyb3d8bbwe!Microsoft.Xbox.App\",\r\n"
        "    \"media player\":   \"shell:AppsFolder\\\\Microsoft.Windows.MediaPlayer32\",\r\n"
        "    \"solitaire\":      \"shell:AppsFolder\\\\Microsoft.MicrosoftSolitaireCollection_8wekyb3d8bbwe!App\",\r\n"
        "}\r\n"
    )
    new_content = content[:start_idx] + new_block + content[end_idx:]
    open('zoya/os/Jarvis_window_CTRL.py', 'w', encoding='utf-8').write(new_content)
    print("SUCCESS: APP_MAPPINGS fully updated!")
    print(f"Replaced chars {start_idx} to {end_idx}")
