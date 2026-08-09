"""
Zoya Memory System
====================
Zoya yahan apni saari yaadein store karti hai —
chahe 1 din baad pucho ya 6 din baad, woh yaad rakhegi.
"""

import os
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import function_tool, RunContext
import httpx

# ─── Project Root (hamesha d:\ai) ─────────────────────────────────────────────
# Path(__file__).resolve() → is file ka absolute path
# .parent → zoya_memory.py ka folder = d:\ai
BASE_DIR = Path(__file__).resolve().parents[2]

# .env hamesha project root se load ho
load_dotenv(dotenv_path=BASE_DIR / ".env")

# ─── API Keys — har kaam ke liye uski sahi key ────────────────────────────────
API_KEYS = {
    # Memory recall ke liye — yaadein dhundhna
    "memory":          os.getenv("OPENROUTER_API_KEY_Memory"),
    # Semantic search ke liye — matlab samajh ke dhundhna
    "search":          os.getenv("OPENROUTER_API_KEY_Semantic_Search"),
    # Tool functions ke liye — save/delete operations
    "tools":           os.getenv("OPENROUTER_API_KEY_GPT4o_Mini_Tools"),
    # Backup tool key agar GPT4o_Mini na kaam kare
    "tools_backup":    os.getenv("OPENROUTER_API_KEY_Claude_Sonnet_Tools"),
    # Last resort fallback
    "fallback":        os.getenv("OPENROUTER_API_KEY"),
}

# ─── Storage ──────────────────────────────────────────────────────────────────
DATA_DIR    = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
MEMORY_FILE = DATA_DIR / "memories.json"     # d:\ai\data\memories.json
LESSONS_FILE = DATA_DIR / "lessons.json"      # d:\ai\data\lessons.json (Learning Log)


# ─── Models — har purpose ke liye sahi model ──────────────────────────────────
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODELS = {
    "memory": "openai/gpt-4o-mini",   # memory recall — fast, smart
    "search": "openai/gpt-4o-mini",   # semantic search
    "tools":  "openai/gpt-4o-mini",   # tool operations
}


# ─── Helpers ──────────────────────────────────────────────────────────────────
def _load_memories() -> list[dict]:
    """memories.json se saari yaadein padhna"""
    if not MEMORY_FILE.exists():
        return []
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_memories(memories: list[dict]):
    """memories.json mein likho"""
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memories, f, ensure_ascii=False, indent=2)


def _get_key(purpose: str) -> str:
    """
    Sahi API key do — purpose ke hisaab se.
    Fallback chain: specific key → tools → tools_backup → fallback
    """
    key = API_KEYS.get(purpose)
    if key:
        return key
    for fallback in ["tools", "tools_backup", "fallback"]:
        key = API_KEYS.get(fallback)
        if key:
            return key
    raise RuntimeError("Koi bhi OpenRouter API key .env mein nahi mili!")


async def _ask_openrouter(system: str, user: str, purpose: str = "memory") -> str:
    """
    OpenRouter se sawaal pucho — sahi key aur model automatically use hoga.
    purpose: 'memory' | 'search' | 'tools'
    """
    api_key = _get_key(purpose)
    model   = MODELS.get(purpose, MODELS["memory"])

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type":  "application/json",
        "HTTP-Referer":  "zoya-agent",
        "X-Title":       "Zoya Memory",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        "max_tokens": 500,
    }
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(OPENROUTER_URL, headers=headers, json=payload)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()


# ─── Tools ────────────────────────────────────────────────────────────────────
@function_tool
async def save_memory(context: RunContext, content: str) -> str:
    """
    Zoya ko kuch yaad dilao — woh ise hamesha ke liye likh legi.

    Args:
        content: Woh baat jo yaad rakhni hai (koi bhi cheez chal sakti hai)
    """
    memories = _load_memories()

    new_memory = {
        "id": len(memories) + 1,
        "content": content,
        "saved_at": datetime.now().isoformat(),
        "saved_at_readable": datetime.now().strftime("%d %B %Y, %I:%M %p"),
    }

    memories.append(new_memory)
    _save_memories(memories)

    return (
        f"✅ Yaad kar li! Maine likha: \"{content}\"\n"
        f"🕐 Waqt: {new_memory['saved_at_readable']}\n"
        f"📚 Ab mere paas kul {len(memories)} yaadein hain."
    )


@function_tool
async def recall_memory(context: RunContext, query: str) -> str:
    """
    Kuch dhundho jo pehle bataya tha — Zoya yaadein khangal ke batayegi.

    Args:
        query: Kya dhundhna hai? (koi bhi sawal ya topic)
    """
    memories = _load_memories()

    if not memories:
        return "Abhi tak koi yaad nahi hai. Pehle kuch batao to main yaad rakh lungi! 😊"

    # Saari memories ek string mein daal do
    memories_text = "\n".join(
        [
            f"[{m['id']}] ({m['saved_at_readable']}): {m['content']}"
            for m in memories
        ]
    )

    system_prompt = (
        "Tu Zoya hai — ek caring, smart AI assistant. "
        "Neeche teri stored memories hain. "
        "User ke sawal ke hisaab se relevant memories dhundh kar Roman Urdu mein jawab de. "
        "Agar koi relevant memory nahi mili to honestly bolo. "
        "Answer short aur natural rakh, jaise dost baat karta hai."
    )

    user_prompt = (
        f"Meri memories:\n{memories_text}\n\n"
        f"User ka sawal: {query}\n\n"
        "Relevant information batao."
    )

    # Stage 1: OPENROUTER_API_KEY_Memory se recall karo
    try:
        answer = await _ask_openrouter(system_prompt, user_prompt, purpose="memory")
        return answer
    except Exception:
        pass

    # Stage 2: OPENROUTER_API_KEY_Semantic_Search se try karo
    try:
        answer = await _ask_openrouter(system_prompt, user_prompt, purpose="search")
        return answer
    except Exception:
        pass

    # Stage 3: Simple keyword search (no API needed)
    query_lower = query.lower()
    matches = [m for m in memories if query_lower in m["content"].lower()]
    if matches:
        result = "Yeh relevant yaadein mili:\n"
        for m in matches:
            result += f"• [{m['saved_at_readable']}] {m['content']}\n"
        return result

    return f"Is topic se related koi yaad nahi mili: '{query}'"


@function_tool
async def list_all_memories(context: RunContext) -> str:
    """
    Saari saved memories ki list dikhao.
    """
    memories = _load_memories()

    if not memories:
        return "Ab tak koi yaad nahi hai. Kuch batao to main yaad rakh lungi! 📝"

    result = f"📚 Mujhe {len(memories)} cheezein yaad hain:\n\n"
    for m in memories:
        result += f"[{m['id']}] 🕐 {m['saved_at_readable']}\n    💬 {m['content']}\n\n"

    return result.strip()


@function_tool
async def delete_memory(context: RunContext, memory_id: int) -> str:
    """
    Koi specific yaad bhool jao (ID number se).

    Args:
        memory_id: Woh memory ka number jo delete karni hai
    """
    memories = _load_memories()

    original_count = len(memories)
    memories = [m for m in memories if m["id"] != memory_id]

    if len(memories) == original_count:
        return f"❌ ID {memory_id} wali koi memory nahi mili."

    _save_memories(memories)
    return f"🗑️ Memory #{memory_id} delete ho gayi. Ab {len(memories)} yaadein baqi hain."


# ─── Self-Learning (Mistakes & Improvements) ───────────────────────────

def _load_lessons() -> list[dict]:
    if not LESSONS_FILE.exists():
        return []
    try:
        with open(LESSONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def _save_lessons(lessons: list[dict]):
    with open(LESSONS_FILE, "w", encoding="utf-8") as f:
        json.dump(lessons, f, ensure_ascii=False, indent=2)

@function_tool
async def save_lesson_learned(context: RunContext, mistake: str, correction: str) -> str:
    """
    Use this when you make a mistake, a tool fails, or the user corrects you. 
    It saves the 'Lesson' so you don't repeat the mistake.
    
    Args:
        mistake: What went wrong? (e.g. 'I used the wrong API key for weather')
        correction: What is the correct way? (e.g. 'Use the OpenWeather key from .env')
    """
    lessons = _load_lessons()
    new_lesson = {
        "id": len(lessons) + 1,
        "mistake": mistake,
        "correction": correction,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    lessons.append(new_lesson)
    _save_lessons(lessons)
    return f"✅ Lesson Learned: Agli baar main '{mistake}' nahi karungi. Yaad rakhungi ke '{correction}' sahi tareeqa hai. Shukriya!"

@function_tool
async def recall_lessons_learned(context: RunContext, topic: str) -> str:
    """
    Check if you have learned any lessons about a specific topic to avoid repeat mistakes.
    
    Args:
        topic: The topic/task you are about to perform (e.g. 'weather', 'search', 'email')
    """
    lessons = _load_lessons()
    if not lessons:
        return "Abhi tak koi seekhi hui galti (lessons) record nahi hui."
    
    # Filter lessons by keyword in mistake or correction
    relevant = [L for L in lessons if topic.lower() in L["mistake"].lower() or topic.lower() in L["correction"].lower()]
    
    if not relevant:
        return f"Topic '{topic}' ke baaray mein koi purani galti ya lesson nahi mila."
    
    res = f"⚠️ Topic '{topic}' ke liye mere paas {len(relevant)} purane lessons hain:\n"
    for L in relevant:
        res += f"- Mistake: {L['mistake']} -> Solve: {L['correction']}\n"
    return res

