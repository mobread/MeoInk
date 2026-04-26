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

THEMES = {
    "dark": {
        "bg": (15, 15, 15),
        "text": (220, 220, 220),
        "dim": (120, 120, 120),
        "accent": (110, 231, 183),
        "divider": (40, 40, 40),
    },
    "light": {
        "bg": (248, 248, 245),
        "text": (20, 20, 20),
        "dim": (100, 100, 100),
        "accent": (0, 120, 70),
        "divider": (200, 200, 200),
    },
}

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


def fetch_and_render_weather(
    units: str = "imperial",
    theme: str = "dark",
    forecast: str = "3day",
) -> bytes:
    units_params = (
        "temperature_unit=fahrenheit&wind_speed_unit=mph"
        if units == "imperial"
        else "temperature_unit=celsius&wind_speed_unit=kmh"
    )
    url = OPEN_METEO_URL.format(units_params=units_params)
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    return _render_weather_card(r.json(), units, theme, forecast)


def _render_weather_card(
    data: dict,
    units: str,
    theme: str = "dark",
    forecast: str = "3day",
) -> bytes:
    colors = THEMES.get(theme, THEMES["dark"])
    current = data["current"]
    daily = data["daily"]
    unit_sym = "°F" if units == "imperial" else "°C"
    speed_unit = "mph" if units == "imperial" else "km/h"

    temp = round(current["temperature_2m"])
    feels = round(current["apparent_temperature"])
    condition = WEATHER_CODES.get(current["weather_code"], "Unknown")
    wind = round(current["windspeed_10m"])
    humidity = current["relative_humidity_2m"]
    hi = round(daily["temperature_2m_max"][0])
    lo = round(daily["temperature_2m_min"][0])

    tz = pytz.timezone("America/Denver")
    now_str = datetime.now(tz).strftime("%-I:%M %p")

    img = Image.new("RGB", DISPLAY_SIZE, colors["bg"])
    d = ImageDraw.Draw(img)

    if forecast == "minimal":
        _draw_minimal(d, temp, hi, lo, condition, unit_sym, colors)
    elif forecast == "today":
        _draw_today(d, temp, feels, condition, wind, humidity, hi, lo,
                    unit_sym, speed_unit, now_str, colors)
    else:
        _draw_3day(d, data, temp, feels, condition, wind, humidity,
                   unit_sym, speed_unit, now_str, colors)

    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def _draw_header(d: ImageDraw.ImageDraw, now_str: str, colors: dict) -> None:
    d.text((30, 24), "Denver, CO", font=_font(18), fill=colors["dim"])
    d.text((770, 24), now_str, font=_font(18), fill=colors["dim"], anchor="ra")
    d.line([(30, 52), (770, 52)], fill=colors["divider"], width=1)


def _draw_3day(d, data, temp, feels, condition, wind, humidity,
               unit_sym, speed_unit, now_str, colors):
    daily = data["daily"]
    _draw_header(d, now_str, colors)

    d.text((30, 65), f"{temp}{unit_sym}", font=_font(96, bold=True), fill=colors["text"])
    d.text((380, 90), condition, font=_font(32, bold=True), fill=colors["accent"])
    d.text((380, 136), f"Feels like {feels}{unit_sym}", font=_font(22), fill=colors["dim"])
    d.text((380, 168), f"Wind {wind} {speed_unit}  ·  Humidity {humidity}%",
           font=_font(20), fill=colors["dim"])

    d.line([(30, 240), (770, 240)], fill=colors["divider"], width=1)

    days = ["Today", "Tomorrow", _day_name(daily["time"][2])]
    col_w = DISPLAY_SIZE[0] // 3
    for i in range(3):
        cx = i * col_w + col_w // 2
        hi = round(daily["temperature_2m_max"][i])
        lo = round(daily["temperature_2m_min"][i])
        cond = WEATHER_CODES.get(daily["weathercode"][i], "Unknown")
        d.text((cx, 268), days[i], font=_font(20, bold=True), fill=colors["text"], anchor="mm")
        d.text((cx, 312), f"L: {lo}{unit_sym}  H: {hi}{unit_sym}",
               font=_font(18), fill=colors["dim"], anchor="mm")
        d.text((cx, 348), cond, font=_font(16), fill=colors["dim"], anchor="mm")
        if i < 2:
            d.line([(col_w * (i + 1), 255), (col_w * (i + 1), 375)],
                   fill=colors["divider"], width=1)


def _draw_today(d, temp, feels, condition, wind, humidity, hi, lo,
                unit_sym, speed_unit, now_str, colors):
    _draw_header(d, now_str, colors)

    # Large temp left-aligned
    d.text((30, 70), f"{temp}{unit_sym}", font=_font(110, bold=True), fill=colors["text"])

    # Conditions right-side
    d.text((380, 100), condition, font=_font(36, bold=True), fill=colors["accent"])
    d.text((380, 150), f"Feels like {feels}{unit_sym}", font=_font(24), fill=colors["dim"])
    d.text((380, 190), f"Wind {wind} {speed_unit}  ·  Humidity {humidity}%",
           font=_font(20), fill=colors["dim"])

    # H/L strip at bottom
    d.line([(30, 320), (770, 320)], fill=colors["divider"], width=1)
    d.text((400, 390), f"L: {lo}{unit_sym}         H: {hi}{unit_sym}",
           font=_font(40, bold=True), fill=colors["text"], anchor="mm")


def _draw_minimal(d, temp, hi, lo, condition, unit_sym, colors):
    # Vertically centered — temp, then H/L, then condition
    d.text((400, 175), f"{temp}{unit_sym}",
           font=_font(130, bold=True), fill=colors["text"], anchor="mm")
    d.text((400, 290), f"L: {lo}{unit_sym}   ·   H: {hi}{unit_sym}",
           font=_font(32), fill=colors["dim"], anchor="mm")
    d.text((400, 355), condition,
           font=_font(26), fill=colors["accent"], anchor="mm")


def _day_name(date_str: str) -> str:
    return datetime.strptime(date_str, "%Y-%m-%d").strftime("%A")
