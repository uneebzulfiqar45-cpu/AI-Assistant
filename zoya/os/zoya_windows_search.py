import os
import win32com.client
from livekit.agents import function_tool, RunContext

@function_tool
async def background_windows_search(context: RunContext, search_term: str) -> str:
    """
    Search quietly and instantly in the background through all windows indexed files and folders.
    Use this when user says "window k sath search karo", "find this file on my pc", etc.

    Args:
        search_term: The keyword or filename to search.
    """
    try:
        conn = win32com.client.Dispatch("ADODB.Connection")
        conn.Open("Provider=Search.CollatorDSO;Extended Properties='Application=Windows';")
        
        # Searching file paths and names via Windows Indexer
        query = f"SELECT System.ItemPathDisplay FROM SystemIndex WHERE System.FileName LIKE '%{search_term}%'"
        
        rs = win32com.client.Dispatch("ADODB.Recordset")
        rs.Open(query, conn)
        
        matches = []
        while not rs.EOF and len(matches) < 30:
            matches.append(rs.Fields.Item("System.ItemPathDisplay").Value)
            rs.MoveNext()
        
        rs.Close()
        conn.Close()
        
        if not matches:
            return f"❌ '{search_term}' se related windows ki list mein kuch nahi mila."
            
        result_str = "\n".join(matches)
        return f"✅ '{search_term}' ki native Windows Search complete hui. Matches:\n{result_str}"
        
    except Exception as e:
        return f"Search error aai achanak: {e}"
