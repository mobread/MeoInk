# MeoInk Design Spec
_2026-04-25_

## Overview

MeoInk is a barebones e-ink display controller for a Raspberry Pi Zero (rpzero01) with a Pimoroni Inky Impression 800×480 7-color display. All rendering and plugin logic runs on pve01; the Pi is a dumb display endpoint. A new "Ink" page in the existing meoctl dashboard provides the UI.

## Architecture

```
pve01
├── MeoInk server (FastAPI, port 8183)
│   ├── Renders images (Pillow, Open-Meteo)
│   ├── Pushes rendered images to the Pi
│   └── Serves current preview to the dashboard
└── Dashboard "Ink" page (React)
    └── Calls MeoInk server API

rpzero01
└── MeoInk client (Flask, port 5000)
    └── Accepts image POST → calls Inky library → updates display
```

## Folder Layout

```
/home/michael/MeoInk/
├── server/
│   ├── main.py          # FastAPI app
│   ├── renderer.py      # Pillow: image resize, weather card
│   ├── pusher.py        # HTTP POST to Pi client
│   └── requirements.txt
├── client/
│   ├── receiver.py      # Flask receiver, Inky display driver
│   └── requirements.txt
└── README.md
```

The dashboard Ink page lives in the existing meoctl dashboard repo at:
`dashboard/src/client/components/InkPage.tsx`

## Pi Client (`client/receiver.py`)

A minimal Flask server running on rpzero01 at port 5000.

**Routes:**
- `POST /display` — accepts a multipart PNG image, writes it to `current.png`, calls the Inky library to push it to the display. Returns `{"ok": true}`.

**Display specs:** Inky Impression, 800×480, 7-color. All images must be delivered pre-rendered at exactly 800×480 — the client does no resizing.

The client is installed as a systemd service (`meoink-client.service`) so it starts on boot.

## MeoInk Server (`server/`)

FastAPI server running on pve01 at port 8183.

**Routes:**

| Method | Path | Input | Output |
|--------|------|-------|--------|
| `POST` | `/render/upload` | multipart PNG/JPG | PNG resized to 800×480 |
| `POST` | `/render/url` | `{url: string}` | PNG fetched + resized to 800×480 |
| `POST` | `/render/weather` | `{units: "imperial"\|"metric"}` (optional, defaults to imperial) | PNG weather card 800×480 |
| `POST` | `/push` | multipart PNG | Forwards to Pi client, returns `{"ok": true}` |
| `GET`  | `/current` | — | `{"timestamp": ISO8601, "type": "upload"\|"url"\|"weather", "image_url": "/current/image.png"}` |

**Renderer (`renderer.py`):**
- Image upload/URL: fetch → Pillow resize/crop to 800×480 (letterbox to preserve aspect ratio)
- Weather: fetch Open-Meteo for lat=39.758, lon=-104.967 (80205 Denver), render a Pillow-drawn weather card — current temp, conditions icon, 3-day forecast

**Pusher (`pusher.py`):**
- `POST http://rpzero01.home.lan:5000/display` with the image as multipart
- Returns success/failure so the dashboard can show push status

## Dashboard Ink Page (`InkPage.tsx`)

A new page added to the existing dashboard, accessible via the "Ink" nav item.

**Layout:** Tabs + Stacked (mobile-first, matches existing dashboard style)

**Three tabs:**

1. **Upload** — drag/drop or file picker → preview → Push to Display
2. **Weather** — location shown as "80205 — Denver, CO", units toggle (Imperial/Metric) → "Render Preview" button → preview → Push to Display  
3. **URL** — text input + Fetch button → preview → Push to Display

**Common elements on every tab:**
- Preview pane (800×480 scaled to fit screen width, aspect-ratio preserved)
- "Push to Display" button (full width, green, disabled until a preview exists)

**Bottom status strip:**
- Thumbnail of currently displayed image
- "rpzero01 · last pushed N ago"
- Reachability dot (green/red, polled from dashboard status)

**API calls:** All rendering and push operations call `http://localhost:8183` (same host, different port). No direct SSH or Pi communication from the browser.

## Data Flow Examples

**Image upload → display:**
1. User picks a file in the Upload tab
2. Dashboard POSTs to `MeoInk /render/upload` → gets back a 800×480 PNG
3. Preview shown in dashboard
4. User clicks Push → dashboard POSTs preview PNG to `MeoInk /push`
5. MeoInk server POSTs to `rpzero01:5000/display`
6. Pi calls Inky library, display updates

**Weather → display:**
1. User clicks "Render Preview" in Weather tab
2. Dashboard calls `MeoInk POST /render/weather`
3. MeoInk fetches Open-Meteo, draws weather card with Pillow, returns PNG
4. Preview shown
5. User clicks Push → same push flow as above

## Port Assignments

| Service | Host | Port |
|---------|------|------|
| MeoInk server | pve01 | 8183 |
| MeoInk client | rpzero01 | 5000 |
| InkyPi (existing) | rpzero01 | 80 |
| InkyPi-dev | pve01 | 8182 |

## Out of Scope (v1)

- Scheduling / playlist rotation (manual push only)
- Multiple display targets
- Display brightness/saturation controls
- Authentication
