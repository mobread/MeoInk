# Pocket Vision Lab

A self-contained MediaPipe Tasks Vision demo that runs on an iPhone's camera.
Three models, switchable live, all inference on-device:

| Mode  | Model                      | Output                                        |
|-------|----------------------------|-----------------------------------------------|
| Hands | Gesture Recognizer         | 21 landmarks/hand (×2), handedness, gesture    |
| Face  | Face Landmarker            | 478-point mesh + expression blendshapes        |
| Pose  | Pose Landmarker (lite)     | 33 body joints + per-joint visibility          |

`index.html` is the whole application — no build step, no framework.

## Running it

```bash
./fetch-assets.sh          # pulls the WASM runtime + model weights (~40 MB)
python3 -m http.server 8099
```

Then open `http://localhost:8099/`. For a phone, serve it over HTTPS — iOS only
grants camera access on a secure origin.

## Why the assets are served locally

The page never fetches from a CDN at runtime. `FilesetResolver` points at
`./wasm`, and model weights are streamed from `./models` with `fetch()` and
handed to MediaPipe as a `modelAssetBuffer`, which is what drives the download
progress bar. This keeps the demo working in sandboxed hosts whose CSP blocks
cross-origin `fetch`/XHR, and means the only third-party request on the page is
the Google Fonts stylesheet.

## iOS notes

- **Safari 16.4+**, HTTPS, and a real tap to start — `getUserMedia` cannot be
  called on page load.
- **The camera is opened before the model downloads.** iOS grants `getUserMedia`
  only while the tap still counts as user activation; awaiting a ~20 MB download
  first lets that activation lapse and the call is refused. It also means a
  blocked camera fails immediately rather than after a long download.
- **Escaping an embedded frame is best-effort.** A host iframe may withhold
  `allow-popups` *and* `allow-top-navigation`, in which case `window.open` and
  `top.location` both silently fail; the Clipboard API can be blocked by
  permissions policy too. The recovery panel tries all three, then falls back to
  a selectable address the viewer can copy by hand.
- `<video playsinline muted autoplay>` — without `playsinline`, iOS takes the
  video fullscreen and the landmark overlay is lost.
- The front camera is mirrored in CSS; the overlay canvas is mirrored with it so
  landmarks stay registered to the image.

## Implementation notes

- `GestureRecognizer` uses `recognizeForVideo()`; the two landmarkers use
  `detectForVideo()`. Mixing these up fails silently every frame.
- The overlay canvas is sized to `video.videoWidth/Height` and shares the
  video's `object-fit: cover`, so normalized landmark coordinates map straight
  onto the displayed crop without manual letterbox math.
- The graph is built against the WebGL delegate and rebuilt on CPU if that
  throws. MediaPipe may still route individual ops to CPU (XNNPACK), so the
  Delegate readout reports what was *requested*.
- Models are fetched lazily — switching modes downloads that mode's weights the
  first time only.
