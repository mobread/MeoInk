# Pocket Vision Lab

On-device MediaPipe vision running on a phone camera. Three models, switchable
live, no frames ever leaving the device:

| Mode  | Model                  | Output                                      |
|-------|------------------------|---------------------------------------------|
| Hands | Gesture Recognizer     | 21 landmarks/hand (x2), handedness, gesture |
| Face  | Face Landmarker        | 478-point mesh + expression blendshapes     |
| Pose  | Pose Landmarker (lite) | 33 body joints + per-joint visibility       |

`index.html` is the entire application: no build step, no framework, no runtime
CDN calls.

## Quick start (desktop)

```bash
./fetch-assets.sh     # WASM runtime + model weights, ~40 MB, untracked
./serve.py            # http://localhost:8099/
```

`localhost` counts as a secure origin, so the camera works without TLS.

## Serving it to a phone

iOS will not grant camera access unless **all** of these hold:

1. **HTTPS with a certificate the device trusts.** A self-signed cert is not
   enough — Safari will load the page and still refuse the camera. Use a real
   certificate (Let's Encrypt via `deploy/Caddyfile`) or a Tailscale/ngrok
   hostname that terminates TLS for you.
2. **Top-level page, not an iframe.** Camera capture is gated by Permissions
   Policy; a host that embeds this page without `allow="camera"` blocks it, and
   opening that host in a new tab does not help because the page is still
   embedded. This is why the demo must be served directly rather than from a
   sandboxed preview.
3. **Safari 16.4+**, and a real tap to start — `getUserMedia` cannot be called
   on page load.

### Deploy

```bash
sudo mkdir -p /opt/pocket-vision-lab
sudo rsync -a --exclude .git ./ /opt/pocket-vision-lab/
cd /opt/pocket-vision-lab && sudo ./fetch-assets.sh

sudo cp deploy/pocket-vision-lab.service /etc/systemd/system/
sudo systemctl enable --now pocket-vision-lab

# TLS in front of it -- edit the hostname first
sudo cp deploy/Caddyfile /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

## Why assets are served locally

The page never fetches from a CDN at runtime. `FilesetResolver` points at
`./wasm`, and model weights are streamed from `./models` with `fetch()` and
handed to MediaPipe as a `modelAssetBuffer`, which is what drives the download
progress bar. This keeps it working in sandboxed hosts whose CSP blocks
cross-origin `fetch`/XHR, and leaves the Google Fonts stylesheet as the only
third-party request on the page.

`serve.py` exists because `http.server` does not know `.wasm` or `.mjs`, and a
wrong `Content-Type` makes the browser refuse to compile either one. Any proxy
in front must not re-encode `.task`/`.wasm` bodies (`no-transform`).

## Implementation notes

- `GestureRecognizer` uses `recognizeForVideo()`; the two landmarkers use
  `detectForVideo()`. Mixing these up fails silently every frame.
- **The camera is opened before the model downloads.** iOS honours
  `getUserMedia` only while the originating tap still counts as user
  activation; awaiting a ~20 MB download first lets that lapse and the call is
  refused. It also surfaces a blocked camera in a second rather than after a
  long download.
- The overlay canvas is sized to `video.videoWidth/Height` and shares the
  video's `object-fit: cover`, so normalized landmark coordinates map straight
  onto the displayed crop with no letterbox math.
- Front camera is mirrored in CSS and the overlay is mirrored with it, so
  landmarks stay registered to the image.
- The graph is built against the WebGL delegate and rebuilt on CPU if that
  throws. MediaPipe may still route individual ops to CPU (XNNPACK), so the
  Delegate readout reports what was *requested*.
- Weights load lazily — switching modes downloads that mode's model once.
- **Escaping an embedded frame is best-effort.** A host iframe may withhold
  `allow-popups` *and* `allow-top-navigation`, so `window.open` and
  `top.location` both fail silently, and the Clipboard API can be blocked by
  permissions policy. The recovery panel tries all three, then falls back to a
  selectable address. Self-hosting avoids the situation entirely.
