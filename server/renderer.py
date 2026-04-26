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


def fetch_and_render_weather(units: str = "imperial") -> bytes:
    units_params = (
        "temperature_unit=fahrenheit&wind_speed_unit=mph"
        if units == "imperial"
        else "temperature_unit=celsius&wind_speed_unit=kmh"
    )
    url = OPEN_METEO_URL.format(units_params=units_params)
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    return _render_weather_card(r.json(), units)


def _render_weather_card(data: dict, units: str) -> bytes:
    img = Image.new("RGB", DISPLAY_SIZE, BG_COLOR)
    d = ImageDraw.Draw(img)

    current = data["current"]
    daily = data["daily"]
    unit_sym = "°F" if units == "imperial" else "°C"
    speed_unit = "mph" if units == "imperial" else "km/h"

    temp = round(current["temperature_2m"])
    feels = round(current["apparent_temperature"])
    condition = WEATHER_CODES.get(current["weather_code"], "Unknown")
    wind = round(current["windspeed_10m"])
    humidity = current["relative_humidity_2m"]

    tz = pytz.timezone("America/Denver")
    now_str = datetime.now(tz).strftime("%-I:%M %p")

    # Header row
    d.text((30, 24), "Denver, CO", font=_font(18), fill=DIM_COLOR)
    d.text((770, 24), now_str, font=_font(18), fill=DIM_COLOR, anchor="ra")
    d.line([(30, 52), (770, 52)], fill=(40, 40, 40), width=1)

    # Current temp (large)
    d.text((30, 65), f"{temp}{unit_sym}", font=_font(96, bold=True), fill=TEXT_COLOR)

    # Current conditions (right of temp)
    d.text((380, 90), condition, font=_font(32, bold=True), fill=ACCENT_COLOR)
    d.text((380, 136), f"Feels like {feels}{unit_sym}", font=_font(22), fill=DIM_COLOR)
    d.text((380, 168), f"Wind {wind} {speed_unit}  ·  Humidity {humidity}%",
           font=_font(20), fill=DIM_COLOR)

    # Divider before forecast
    d.line([(30, 240), (770, 240)], fill=(40, 40, 40), width=1)

    # 3-day forecast
    days = ["Today", "Tomorrow", _day_name(daily["time"][2])]
    col_w = DISPLAY_SIZE[0] // 3
    for i in range(3):
        cx = i * col_w + col_w // 2
        hi = round(daily["temperature_2m_max"][i])
        lo = round(daily["temperature_2m_min"][i])
        cond = WEATHER_CODES.get(daily["weathercode"][i], "Unknown")
        d.text((cx, 268), days[i], font=_font(20, bold=True), fill=TEXT_COLOR, anchor="mm")
        d.text((cx, 312), f"H: {hi}{unit_sym}  L: {lo}{unit_sym}",
               font=_font(18), fill=DIM_COLOR, anchor="mm")
        d.text((cx, 348), cond, font=_font(16), fill=DIM_COLOR, anchor="mm")
        if i < 2:
            d.line([(col_w * (i + 1), 255), (col_w * (i + 1), 375)],
                   fill=(40, 40, 40), width=1)

    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def _day_name(date_str: str) -> str:
    return datetime.strptime(date_str, "%Y-%m-%d").strftime("%A")
