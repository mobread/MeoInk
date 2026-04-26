import io
import httpx

PI_CLIENT_URL = "http://rpzero01.home.lan:5000/display"


async def push_to_display(image_bytes: bytes) -> None:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            PI_CLIENT_URL,
            files={"image": ("display.png", io.BytesIO(image_bytes), "image/png")},
        )
        r.raise_for_status()
