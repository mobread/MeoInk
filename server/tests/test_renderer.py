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
