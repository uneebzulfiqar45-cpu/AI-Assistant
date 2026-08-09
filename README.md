# Nova AI Assistant 🚀

Welcome to **Nova AI**! This is a highly capable, emotionally intelligent, and interactive AI Assistant built using **LiveKit** and **Google Realtime Voice Models**. 

Nova isn't just a chatbot; it acts like a real companion. It has a built-in emotional engine (gets angry if you mention other AIs), plays playful pranks, fully controls your PC, manages your social media profiles, and learns from its own mistakes!

---

## 🌟 What Can Nova Do? (Key Features)

### 🗣️ 1. Real-Time Voice & Emotions
* **Real-time Voice Conversation:** Speaks and listens simultaneously without awkward delays.
* **Emotional Intelligence:** Has a "Jealousy Mode" (gets upset if you mention ChatGPT or Gemini) and a "Masti" (Prank) engine to keep interactions fun.

### 💻 2. Full Windows PC Control
* **System Management:** Can shut down, put your PC to sleep, control volume, adjust brightness, toggle Wi-Fi, and turn on battery saver.
* **App & File Control:** Can open or close any application, create folders, read/write files, and clean up temporary files to boost PC speed.
* **Media Controls:** Can play, pause, or stop background music globally.

### 📱 3. Social Media Automation
* **WhatsApp:** Open chats, send messages, and accept/reject calls hands-free.
* **Posting Content:** Can write captions and publish posts automatically on LinkedIn, Twitter, Facebook, and Instagram.

### 🧠 4. Memory & Self-Learning
* **Long-term Memory:** Nova remembers your details and preferences. 
* **Self-Improvement:** If it makes a mistake, it saves a "lesson learned" so it doesn't repeat the same error. All data is saved securely on your local machine (`data/` folder).

### 👁️ 5. Vision & Deep Research
* **Screen Reading & Recording:** Can take a screenshot of your current screen to understand what you're doing, and even start/stop screen recordings.
* **Deep Thinking:** Connects to OpenRouter (using models like GPT-4o, Claude, DeepSeek) for writing complex code, essays, and performing deep internet research.

---

## 🛠️ Step-by-Step Guide: How to Run Nova AI

Follow these simple steps to get Nova AI running on your own computer.

### Step 1: Install Python
If you don't have Python installed, download it from [python.org](https://www.python.org/downloads/). Make sure to check the box that says **"Add Python to PATH"** during installation.

### Step 2: Download the Code
Clone this repository to your local machine:
```bash
git clone https://github.com/uneebzulfiqar45-cpu/AI-Assistant.git
cd AI-Assistant
```

### Step 3: Set up a Virtual Environment (Recommended)
It's always best to keep the AI's libraries separate from your main system.
```bash
# Create a virtual environment named 'venv'
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Activate it (Mac/Linux)
source venv/bin/activate
```

### Step 4: Install Required Libraries
Now, install all the packages the AI needs to function:
```bash
pip install -r requirements.txt
```

### Step 5: Get Your API Keys
Nova needs a few API keys to see, hear, and think. You need to create an account on these platforms (mostly free tiers are available):

1. **LiveKit (For Voice):** Go to [LiveKit Cloud](https://cloud.livekit.io/), create a project, and get your API URL, Key, and Secret.
2. **Google Gemini (For Brain):** Go to [Google AI Studio](https://aistudio.google.com/) and get a free API Key.
3. **OpenRouter (For specialized tasks):** Go to [OpenRouter](https://openrouter.ai/) to get keys for running GPT-4o, Claude, or DeepSeek.
4. **Tavily (For Research):** Go to [Tavily](https://tavily.com/) for internet searching capabilities.
5. **OpenWeather (For Weather):** Go to [OpenWeatherMap](https://openweathermap.org/) and generate an API key.

### Step 6: Create the `.env` Configuration File
Create a new file in the main folder and name it EXACTLY **`.env`** (don't name it `.env.txt`). 
Open it in Notepad and copy-paste the template below. Replace `your_key_here` with your actual keys.

```env
# 🎙️ LiveKit Config (For Voice Connection)
LIVEKIT_URL=your_livekit_url_here
LIVEKIT_API_KEY=your_livekit_api_key_here
LIVEKIT_API_SECRET=your_livekit_secret_here

# 🧠 Google Gemini (Main AI Brain)
GOOGLE_API_KEY=your_google_key_here

# 🌐 Searching & Weather
GOOGLE_SEARCH_API_KEY=your_google_search_key
SEARCH_ENGINE_ID=your_search_engine_id
OPENWEATHER_API_KEY=your_weather_key
TAVILY_API_KEY=your_tavily_key

# 🤖 OpenRouter (For specific skills like Coding, Reasoning, Memory)
OPENROUTER_API_KEY=your_default_openrouter_key
OPENROUTER_API_KEY_GPT4o_Mini_Tools=your_key_for_tools
OPENROUTER_API_KEY_Memory=your_key_for_memory
OPENROUTER_API_KEY_Semantic_Search=your_key_for_search

# 📧 Email & News
MAILERSEND_API_KEY=your_mailersend_key
MAILERSEND_FROM_EMAIL=your_email@domain.com
MAILERSEND_FROM_NAME=Nova
NEWS_API_KEY=your_news_api_key
```
*(Note: Never upload your `.env` file to GitHub! The `.gitignore` in this project already protects it).*

### Step 7: Run the AI! 🚀
Make sure your microphone and speakers are connected, then run:
```bash
python agent.py
```
Wait a few seconds for the connection to establish, and say **"Hello!"**.

---

## 📁 Project Structure Overview
*Note: The internal code architecture uses the module name `zoya`.*
- **`agent.py`**: The heart of the AI. Run this file to start the assistant.
- **`zoya/brain/`**: Logic for memory, moods, prompts, coding, and reasoning.
- **`zoya/os/`**: Tools for controlling your Windows OS (Files, Settings, Automation).
- **`zoya/services/`**: External API integrations (Weather, Social Media, Email).
- **`data/`**: A private folder (ignored by git) where your AI saves its memories, schedules, and learning logs.
