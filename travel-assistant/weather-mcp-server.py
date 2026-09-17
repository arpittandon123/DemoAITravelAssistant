from fastmcp import FastMCP
import random
import httpx

# Initialize Weather MCP Server
mcp = FastMCP("Singapore Weather Server")

@mcp.tool()
async def get_singapore_weather_forecast(days: int = 3) -> str:
    """
    Retrieves real-time weather forecast for Singapore for the next N days.
    To be used when user asks anything related to weather or forecast in Singapore.
    """
    # Returns day-by-day temperature, rainfall probability, and condition summary.
    # Simulated realistic live weather data
    # forecast_data = [
    #     {"day": "Day 1 (Tomorrow)", "temp": "28°C - 31°C", "condition": "Scattered Thunderstorms in Afternoon", "rain_chance": "70%", "recommended": "Indoor afternoon activities"},
    #     {"day": "Day 2", "temp": "26°C - 30°C", "condition": "Heavy Rain expected between 1 PM - 5 PM", "rain_chance": "85%", "recommended": "Plan indoor museums/attractions during midday"},
    #     {"day": "Day 3", "temp": "27°C - 32°C", "condition": "Partly Cloudy with clear skies", "rain_chance": "20%", "recommended": "Great for outdoor sights & Sentosa Island"}
    # ]

    # selected_days = forecast_data[:min(days, 3)]
    
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 1.3521,
        "longitude": 103.8198,
        "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_probability_max", "weather_code"],
        "timezone": "Asia/Singapore",
        "forecast_days": min(days, 7)
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()

        daily = data.get("daily", {})
        dates = daily.get("time", [])
        max_temps = daily.get("temperature_2m_max", [])
        min_temps = daily.get("temperature_2m_min", [])
        rain_chances = daily.get("precipitation_probability_max", [])
    
        result = "=== REAL-TIME WEATHER FORECAST (Source: MCP Weather Tool) ===\n"

        for i in range(len(dates)):
            rain_prob = rain_chances[i]
            advice = "Indoor alternatives recommended during mid-day" if rain_prob > 50 else "Good for outdoor activities"
            result += f"- {dates[i]}: Temp {min_temps[i]}°C to {max_temps[i]}°C | Rain Chance: {rain_prob}% | Note: {advice}\n"

    # for d in selected_days:
    #     result += f"- {d['day']}: {d['condition']} | Temp: {d['temp']} | Rain Chance: {d['rain_chance']} | Advice: {d['recommended']}\n"
    
        return result

    except Exception as e:
        return f"Error fetching live weather: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="stdio")