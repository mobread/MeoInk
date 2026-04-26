# server/tests/test_renderer.py
import io
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from PIL import Image
from renderer import resize_image

def _png(w: int, h: int) -> bytes:
    img = Image.new("RGB", (w, h), (100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()

def test_resize_landscape_letterboxes_to_display():
    result = resize_image(_png(1200, 800))
    out = Image.open(io.BytesIO(result))
    assert out.size == (800, 480)

def test_resize_portrait_letterboxes_to_display():
    result = resize_image(_png(400, 600))
    out = Image.open(io.BytesIO(result))
    assert out.size == (800, 480)

def test_resize_exact_size_passes_through():
    result = resize_image(_png(800, 480))
    out = Image.open(io.BytesIO(result))
    assert out.size == (800, 480)

def test_resize_returns_png_bytes():
    result = resize_image(_png(640, 480))
    assert result[:4] == b'\x89PNG'

from unittest.mock import patch, MagicMock
from renderer import _render_weather_card, fetch_and_render_weather

MOCK_DATA = {
    "current": {
        "temperature_2m": 72.3,
        "apparent_temperature": 68.1,
        "weather_code": 2,
        "windspeed_10m": 8.4,
        "relative_humidity_2m": 45,
    },
    "daily": {
        "time": ["2026-04-25", "2026-04-26", "2026-04-27"],
        "weathercode": [2, 1, 61],
        "temperature_2m_max": [78.0, 82.0, 65.0],
        "temperature_2m_min": [55.0, 58.0, 50.0],
    },
}

def test_render_weather_card_returns_800x480_png():
    result = _render_weather_card(MOCK_DATA, "imperial")
    out = Image.open(io.BytesIO(result))
    assert out.size == (800, 480)
    assert result[:4] == b'\x89PNG'

def test_render_weather_card_metric_units():
    result = _render_weather_card(MOCK_DATA, "metric")
    out = Image.open(io.BytesIO(result))
    assert out.size == (800, 480)

def test_fetch_and_render_weather_calls_open_meteo():
    mock_resp = MagicMock()
    mock_resp.json.return_value = MOCK_DATA
    mock_resp.raise_for_status = MagicMock()
    with patch("renderer.requests.get", return_value=mock_resp) as mock_get:
        result = fetch_and_render_weather("imperial")
        assert mock_get.called
        url_called = mock_get.call_args[0][0]
        assert "open-meteo.com" in url_called
        assert "fahrenheit" in url_called
    out = Image.open(io.BytesIO(result))
    assert out.size == (800, 480)
