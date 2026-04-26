from flask import Flask, request, jsonify
import os

app = Flask(__name__)
IMAGE_PATH = os.path.join(os.path.dirname(__file__), "current.png")

@app.post("/display")
def display():
    if "image" not in request.files:
        return jsonify({"error": "no image"}), 400

    image_bytes = request.files["image"].read()

    with open(IMAGE_PATH, "wb") as f:
        f.write(image_bytes)

    try:
        from PIL import Image
        from inky.auto import auto
        inky = auto()
        img = Image.open(IMAGE_PATH)
        inky.set_image(img, saturation=0.5)
        inky.show()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
