from flask import Flask, request, jsonify
import os
import threading

app = Flask(__name__)
IMAGE_PATH = os.path.join(os.path.dirname(__file__), "current.png")


def _update_display(path):
    try:
        from PIL import Image
        from inky.auto import auto
        inky = auto()
        img = Image.open(path)
        inky.set_image(img, saturation=0.5)
        inky.show()
    except Exception:
        pass


@app.post("/display")
def display():
    if "image" not in request.files:
        return jsonify({"error": "no image"}), 400

    image_bytes = request.files["image"].read()

    with open(IMAGE_PATH, "wb") as f:
        f.write(image_bytes)

    threading.Thread(target=_update_display, args=(IMAGE_PATH,), daemon=True).start()

    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
