import io
import json
from pathlib import Path
from datetime import datetime, timezone

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel

from renderer import resize_image, fetch_and_render_weather

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

STATE_DIR = Path(__file__).parent
STATE_IMAGE = STATE_DIR / "current.png"
STATE_META = STATE_DIR / "current_meta.json"


def _save_state(image_bytes: bytes, content_type: str) -> None:
    STATE_IMAGE.write_bytes(image_bytes)
    STATE_META.write_text(json.dumps({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": content_type,
    }))


class UrlRequest(BaseModel):
    url: str


@app.post("/render/upload")
async def render_upload(file: UploadFile = File(...)):
    data = await file.read()
    try:
        result = resize_image(data)
    except Exception as e:
        raise HTTPException(400, str(e))
    return Response(content=result, media_type="image/png")


@app.post("/render/url")
async def render_url(body: UrlRequest):
    import httpx
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            r = await client.get(body.url)
            r.raise_for_status()
        except Exception as e:
            raise HTTPException(400, f"Failed to fetch URL: {e}")
    try:
        result = resize_image(r.content)
    except Exception as e:
        raise HTTPException(400, f"Not a valid image: {e}")
    return Response(content=result, media_type="image/png")


class WeatherRequest(BaseModel):
    units: str = "imperial"


@app.post("/render/weather")
async def render_weather(body: WeatherRequest = WeatherRequest()):
    try:
        result = fetch_and_render_weather(body.units)
    except Exception as e:
        raise HTTPException(500, str(e))
    return Response(content=result, media_type="image/png")


@app.get("/health")
async def health():
    return {"ok": True}
