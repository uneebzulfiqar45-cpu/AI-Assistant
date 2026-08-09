import os
import requests
import logging
from dotenv import load_dotenv
from livekit.agents import function_tool  # ✅ Correct decorator

load_dotenv()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def detect_city_by_ip() -> str:
    try:
        logger.info("IP ke zariye shehar detect karne ki koshish ki ja rahi hai")
        ip_info = requests.get("https://ipapi.co/json/").json()
        city = ip_info.get("city")
        if city:
            logger.info(f"IP se shehar Detect kiya gaya: {city}")
            return city
        else:
            logger.warning("City detect karne mein vifal, default 'Delhi' istemal kiya ja raha hai.")
            return "Delhi"
    except Exception as e:
        logger.error(f"IP se city detect karne mein error aya: {e}")
        return "Delhi"

@function_tool
async def get_weather(city: str = "") -> str:
    
    api_key = os.getenv("OPENWEATHER_API_KEY")

    if not api_key:
        logger.error("OpenWeather API key missing hai.")
        return "Environment variables mein OpenWeather API key nahi mili."

    if not city:
        city = detect_city_by_ip()

    logger.info(f"City ke liye weather fetch kiya ja raha hai: {city}")
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric"
    }

    try:
        response = requests.get(url, params=params)
        if response.status_code != 200:
            logger.error(f"OpenWeather API mein error aya: {response.status_code} - {response.text}")
            return f"Error: {city} ke liye weather fetch nahi kar paye. Kripya city name check karein."

        data = response.json()
        weather = data["weather"][0]["description"].title()
        temperature = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        wind_speed = data["wind"]["speed"]

        result = (f"Weather in {city}:\n"
                  f"- Condition: {weather}\n"
                  f"- Temperature: {temperature}°C\n"
                  f"- Humidity: {humidity}%\n"
                  f"- Wind Speed: {wind_speed} m/s")

        logger.info(f"Weather result: \n{result}")
        return result

    except Exception as e:
        logger.exception(f"Weather fetch karte samay exception aya: {e}")
        return "Weather fetch karte samay ek error aya"
    
