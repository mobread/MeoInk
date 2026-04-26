import io
import json
from pathlib import Path
from datetime import datetime, timezone

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel

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


@app.get("/health")
async def health():
    return {"ok": True}
