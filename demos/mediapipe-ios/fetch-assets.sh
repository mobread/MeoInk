#!/usr/bin/env bash
# Downloads the MediaPipe runtime + model weights next to index.html so the demo
# can be served locally. ~40 MB total; these are deliberately not committed.
set -euo pipefail
cd "$(dirname "$0")"

TASKS_VISION_VERSION="1.0.1"
MODEL_BASE="https://storage.googleapis.com/mediapipe-models"

mkdir -p wasm models

echo "==> @mediapipe/tasks-vision ${TASKS_VISION_VERSION}"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
curl -fsSL -o "$tmp/tv.tgz" \
  "https://registry.npmjs.org/@mediapipe/tasks-vision/-/tasks-vision-${TASKS_VISION_VERSION}.tgz"
tar xzf "$tmp/tv.tgz" -C "$tmp"
cp "$tmp/package/vision_bundle.mjs" .
cp "$tmp/package/wasm/vision_wasm_internal.js" \
   "$tmp/package/wasm/vision_wasm_internal.wasm" \
   "$tmp/package/wasm/vision_wasm_nosimd_internal.js" \
   "$tmp/package/wasm/vision_wasm_nosimd_internal.wasm" wasm/

echo "==> model weights"
for spec in \
  "gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task" \
  "face_landmarker/face_landmarker/float16/1/face_landmarker.task" \
  "pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
do
  name="$(basename "$spec")"
  echo "    $name"
  curl -fsSL -o "models/$name" "${MODEL_BASE}/${spec}"
done

echo
echo "Done. Serve over HTTPS (or localhost) and open index.html:"
echo "    python3 -m http.server 8099   # then http://localhost:8099/"
