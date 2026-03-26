import httpx
from fastapi import APIRouter

router = APIRouter(prefix="/weather", tags=["weather"])

@router.get("")
async def get_weather(lat: float = 52.52, lon: float = 13.41):
    """
    Fetch current weather using Open-Meteo (free, no API key needed).
    Defaults to Berlin; the frontend passes the user's coordinates.
    """
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,apparent_temperature,weather_code,"
        "wind_speed_10m,relative_humidity_2m,precipitation"
        "&temperature_unit=celsius"
        "&wind_speed_unit=mph"
        "&timezone=auto"
    )
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()

    current = data["current"]

    # Map WMO weather codes to a human-readable description + emoji
    code = current.get("weather_code", 0)
    description, emoji = _wmo_description(code)

    return {
        "temperature": current["temperature_2m"],
        "feels_like": current["apparent_temperature"],
        "humidity": current["relative_humidity_2m"],
        "wind_speed": current["wind_speed_10m"],
        "precipitation": current["precipitation"],
        "description": description,
        "emoji": emoji,
        "unit": "°C",
        "timezone": data.get("timezone", ""),
    }


def _wmo_description(code: int) -> tuple[str, str]:
    table = {
        0: ("Clear sky", "☀️"),
        1: ("Mainly clear", "🌤️"),
        2: ("Partly cloudy", "⛅"),
        3: ("Overcast", "☁️"),
        45: ("Foggy", "🌫️"),
        48: ("Icy fog", "🌫️"),
        51: ("Light drizzle", "🌦️"),
        53: ("Moderate drizzle", "🌦️"),
        55: ("Dense drizzle", "🌧️"),
        61: ("Slight rain", "🌧️"),
        63: ("Moderate rain", "🌧️"),
        65: ("Heavy rain", "🌧️"),
        71: ("Slight snow", "❄️"),
        73: ("Moderate snow", "❄️"),
        75: ("Heavy snow", "❄️"),
        77: ("Snow grains", "❄️"),
        80: ("Slight showers", "🌦️"),
        81: ("Moderate showers", "🌧️"),
        82: ("Violent showers", "⛈️"),
        85: ("Slight snow showers", "🌨️"),
        86: ("Heavy snow showers", "🌨️"),
        95: ("Thunderstorm", "⛈️"),
        96: ("Thunderstorm + hail", "⛈️"),
        99: ("Thunderstorm + heavy hail", "⛈️"),
    }
    return table.get(code, ("Unknown", "🌡️"))
