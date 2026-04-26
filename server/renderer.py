import io
import requests
from PIL import Image, ImageDraw, ImageFont
import pytz
from datetime import datetime

DISPLAY_SIZE = (800, 480)
BG_COLOR = (15, 15, 15)
TEXT_COLOR = (220, 220, 220)
DIM_COLOR = (120, 120, 120)
ACCENT_COLOR = (110, 231, 183)

WEATHER_CODES = {
    0: "Clear", 1: "Mostly Clear", 2: "Partly Cloudy", 3: "Overcast",
    45: "Foggy", 48: "Icy Fog",
    51: "Light Drizzle", 53: "Drizzle", 55: "Heavy Drizzle",
    61: "Light Rain", 63: "Rain", 65: "Heavy Rain",
    71: "Light Snow", 73: "Snow", 75: "Heavy Snow",
    80: "Rain Showers", 81: "Rain Showers", 82: "Heavy Showers",
    95: "Thunderstorm", 96: "Thunderstorm",
}

OPEN_METEO_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude=39.758&longitude=-104.967"
    "&current=temperature_2m,apparent_temperature,weather_code,windspeed_10m,relative_humidity_2m"
    "&daily=weathercode,temperature_2m_max,temperature_2m_min"
    "&timezone=America%2FDenver"
    "&forecast_days=3"
    "&{units_params}"
)


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    try:
        path = "/usr/share/fonts/truetype/dejavu/DejaVuSans{}.ttf".format(
            "-Bold" if bold else ""
        )
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def resize_image(image_bytes: bytes) -> bytes:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img.thumbnail(DISPLAY_SIZE, Image.LANCZOS)
    canvas = Image.new("RGB", DISPLAY_SIZE, BG_COLOR)
    x = (DISPLAY_SIZE[0] - img.width) // 2
    y = (DISPLAY_SIZE[1] - img.height) // 2
    canvas.paste(img, (x, y))
    buf = io.BytesIO()
    canvas.save(buf, "PNG")
    return buf.getvalue()
