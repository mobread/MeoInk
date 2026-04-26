import io
import requests
from PIL import Image, ImageDraw, ImageFont
import pytz
from datetime import datetime, timedelta

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
    "&hourly=temperature_2m"
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

    hourly = data.get("hourly") if forecast in ("minimal", "today") else None

    if forecast == "minimal":
        _draw_minimal(d, temp, hi, lo, condition, unit_sym, colors, hourly=hourly)
    elif forecast == "today":
        _draw_today(d, temp, feels, condition, wind, humidity, hi, lo,
                    unit_sym, speed_unit, now_str, colors, hourly=hourly)
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
                unit_sym, speed_unit, now_str, colors, hourly=None):
    _draw_header(d, now_str, colors)

    # Large temp left-aligned
    d.text((30, 70), f"{temp}{unit_sym}", font=_font(110, bold=True), fill=colors["text"])

    # Conditions right-side
    d.text((380, 100), condition, font=_font(36, bold=True), fill=colors["accent"])
    d.text((380, 150), f"Feels like {feels}{unit_sym}", font=_font(24), fill=colors["dim"])
    d.text((380, 190), f"Wind {wind} {speed_unit}  ·  Humidity {humidity}%",
           font=_font(20), fill=colors["dim"])

    if hourly:
        # Hourly graph in the space between detail text and H/L strip
        _draw_hourly_graph(d, hourly, unit_sym, colors,
                           x0=30, y0=218, width=740, height=95)

    # H/L strip at bottom
    d.line([(30, 320), (770, 320)], fill=colors["divider"], width=1)
    d.text((400, 390), f"L: {lo}{unit_sym}         H: {hi}{unit_sym}",
           font=_font(40, bold=True), fill=colors["text"], anchor="mm")


def _draw_hourly_graph(
    d: ImageDraw.ImageDraw,
    hourly: dict,
    unit_sym: str,
    colors: dict,
    x0: int,
    y0: int,
    width: int,
    height: int,
) -> None:
    """Embed a compact temperature forecast line graph using PIL."""
    tz = pytz.timezone("America/Denver")
    now = datetime.now(tz).replace(tzinfo=None)
    today_9am = now.replace(hour=9, minute=0, second=0, microsecond=0)
    total_hours = 15  # 9am → midnight

    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])

    data_pts = []
    for t_str, temp in zip(times, temps):
        dt = datetime.fromisoformat(t_str)
        offset = (dt - today_9am).total_seconds() / 3600
        if 0 <= offset <= total_hours:
            data_pts.append((offset, round(temp)))

    if len(data_pts) < 2:
        return

    offsets, t_vals = zip(*data_pts)
    t_vals = list(t_vals)
    t_min = min(t_vals)
    t_max = max(t_vals)
    t_range = max(t_max - t_min, 1)

    left_pad = 54   # space for y-axis labels
    pad_top = 18
    pad_bottom = 24
    graph_w = width - left_pad
    graph_h = height - pad_top - pad_bottom

    def to_xy(offset, temp):
        x = x0 + left_pad + int(offset / total_hours * graph_w)
        y = y0 + pad_top + int((1 - (temp - t_min) / t_range) * graph_h)
        return (x, y)

    pts = [to_xy(off, t) for off, t in zip(offsets, t_vals)]
    baseline_y = y0 + height - pad_bottom
    graph_left_x = x0 + left_pad
    graph_top_y = y0 + pad_top

    # Filled area under the line (muted accent)
    fill_color = tuple(max(0, int(c * 0.15)) for c in colors["accent"])
    poly = [(pts[0][0], baseline_y), *pts, (pts[-1][0], baseline_y)]
    d.polygon(poly, fill=fill_color)

    # Line
    for i in range(len(pts) - 1):
        d.line([pts[i], pts[i + 1]], fill=colors["accent"], width=2)

    # Dots at each hour
    DOT_R = 3
    for pt in pts:
        d.ellipse([pt[0]-DOT_R, pt[1]-DOT_R, pt[0]+DOT_R, pt[1]+DOT_R], fill=colors["accent"])

    label_font = _font(16)

    # Y-axis: reference lines + min/max labels
    d.line([(graph_left_x, graph_top_y), (x0 + width, graph_top_y)],
           fill=colors["divider"], width=1)
    d.line([(graph_left_x, baseline_y), (x0 + width, baseline_y)],
           fill=colors["divider"], width=1)
    d.text((graph_left_x - 4, graph_top_y), f"{t_max}{unit_sym}",
           font=label_font, fill=colors["dim"], anchor="rm")
    d.text((graph_left_x - 4, baseline_y), f"{t_min}{unit_sym}",
           font=label_font, fill=colors["dim"], anchor="rm")

    # X-axis labels every 3 hours: 9am → 12am
    tick_offsets = [0, 3, 6, 9, 12, 15]
    tick_labels  = ["9am", "12pm", "3pm", "6pm", "9pm", "12am"]
    for off, lbl in zip(tick_offsets, tick_labels):
        x = graph_left_x + int(off / total_hours * graph_w)
        d.text((x, baseline_y + 3), lbl, font=label_font, fill=colors["dim"], anchor="mt")

    # Current time marker — vertical line from top to bottom of graph area
    now_offset = (now - today_9am).total_seconds() / 3600
    if 0 <= now_offset <= total_hours:
        now_x = graph_left_x + int(now_offset / total_hours * graph_w)
        d.line([(now_x, graph_top_y), (now_x, baseline_y)],
               fill=colors["text"], width=1)
        # Small triangle / tick at top to mark position
        d.polygon([(now_x - 4, graph_top_y - 1),
                   (now_x + 4, graph_top_y - 1),
                   (now_x, graph_top_y + 5)],
                  fill=colors["text"])


def _draw_minimal(d, temp, hi, lo, condition, unit_sym, colors, hourly=None):
    # Shift text up to leave room for the hourly graph at the bottom
    d.text((400, 120), f"{temp}{unit_sym}",
           font=_font(130, bold=True), fill=colors["text"], anchor="mm")
    d.text((400, 235), f"L: {lo}{unit_sym}   ·   H: {hi}{unit_sym}",
           font=_font(32), fill=colors["dim"], anchor="mm")
    d.text((400, 290), condition,
           font=_font(26), fill=colors["accent"], anchor="mm")
    if hourly:
        d.line([(30, 318), (770, 318)], fill=colors["divider"], width=1)
        _draw_hourly_graph(d, hourly, unit_sym, colors,
                           x0=30, y0=322, width=740, height=130)


def _day_name(date_str: str) -> str:
    return datetime.strptime(date_str, "%Y-%m-%d").strftime("%A")
