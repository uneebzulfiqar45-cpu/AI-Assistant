# Zoya AI Assistant 🚀

Zoya is a highly capable, emotional, and interactive AI Assistant built using **LiveKit** and **Google Realtime Voice Models (Aoede)**. Zoya goes beyond just answering questions—she has moods, gets jealous, plays pranks, controls your PC, manages your social media, and learns from her mistakes!

## 🌟 Key Features

1. **Voice Interaction & Emotion:** Talks to you in real-time. Has a "Jealousy Mode" (gets angry if you mention other AIs) and a "Masti" engine for random playful pranks.
2. **PC & OS Control:** Opens/closes apps, manages files/folders, controls volume, brightness, battery saver, Wi-Fi, and can even put your PC to sleep or shut it down.
3. **Social Media Automation:** Can post on LinkedIn, Twitter, Facebook, Instagram. Can also open WhatsApp, send messages, and accept/reject calls.
4. **Memory & Self-Learning:** Zoya remembers what you tell her and learns from her mistakes (`save_memory`, `save_lesson_learned`). Memory is stored locally.
5. **Vision & Screen Recording:** Can take screenshots, read your screen, and record videos.
6. **Deep Research & Coding:** Uses OpenRouter to connect to various LLMs (Claude, GPT-4o, DeepSeek, etc.) for specialized tasks like coding, deep reasoning, and creative writing.
7. **Emails & News:** Can send emails (Brevo/MailerSend) and fetch the latest news and weather updates.

## 🛠️ How to Run Zoya

### 1. Install Dependencies
Make sure you have Python installed. Then, run the following command in your terminal to install all required libraries:
```bash
pip install -r requirements.txt
```

### 2. Create the `.env` File
You need to create a file named exactly `.env` in the root folder (`d:\ai\.env`). **DO NOT upload this file anywhere!**
Inside the `.env` file, you need to add your API Keys. 

Here is the template for your `.env` file:

```env
# LiveKit Config (For Voice Connection)
LIVEKIT_URL=your_livekit_url_here
LIVEKIT_API_KEY=your_livekit_api_key_here
LIVEKIT_API_SECRET=your_livekit_secret_here

# Google Gemini (Main AI Brain)
GOOGLE_API_KEY=your_google_key_here

# Searching & Weather
GOOGLE_SEARCH_API_KEY=your_google_search_key
SEARCH_ENGINE_ID=your_search_engine_id
OPENWEATHER_API_KEY=your_weather_key
TAVILY_API_KEY=your_tavily_key

# OpenRouter (For specific skills like Coding, Reasoning, Memory)
OPENROUTER_API_KEY=your_default_openrouter_key
OPENROUTER_API_KEY_GPT4o_Mini_Tools=your_key_for_tools
OPENROUTER_API_KEY_Memory=your_key_for_memory
OPENROUTER_API_KEY_Semantic_Search=your_key_for_search
# (Add other specific OpenRouter keys as needed based on agent.py)

# Email & News
MAILERSEND_API_KEY=your_mailersend_key
MAILERSEND_FROM_EMAIL=your_email@domain.com
MAILERSEND_FROM_NAME=Zoya
NEWS_API_KEY=your_news_api_key

# Music / Lyrics
genius_API_KEY_Song=your_genius_key
```

*(Note: You can leave the ones blank that you don't use right now, but LiveKit and Google/OpenRouter keys are essential.)*

### 3. Start Zoya
Once the `.env` file is ready and dependencies are installed, just run:
```bash
python agent.py
```
Zoya will start listening to you!

## 📁 Project Structure
- `agent.py`: The main entry point where Zoya's brain and LiveKit connection are initialized.
- `zoya/brain/`: Contains logic for Zoya's memory, moods, prompts, coding, and reasoning.
- `zoya/os/`: Contains tools for controlling the Windows OS (Search, File Explorer, Hardware settings).
- `zoya/services/`: Contains API integrations (Weather, Google Search, Social Media, Email, etc.).
- `data/`: (Ignored in Git) Stores local memory (`memories.json`), schedule, and mood states.

---
**Disclaimer:** Keep your `.env` file safe and never commit it to public repositories.
