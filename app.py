import os, base64, exifread
from flask import Flask, request, render_template_string
from PIL import Image
from openai import OpenAI

app = Flask(__name__)

# Read API key safely from environment variable
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>AI Image Analyzer</title>
<style>
body { font-family: Arial; margin: 40px; }
.box { border: 1px solid #ddd; padding: 20px; border-radius: 8px; }
pre { background:#f4f4f4; padding:10px; }
</style>
</head>
<body>

<h2>Upload Image for AI Summary + Metadata</h2>

<form method="post" enctype="multipart/form-data">
<input type="file" name="image" required>
<button>Analyze Image</button>
</form>

{% if summary %}
<div class="box">
<h3>🧠 AI Image Summary</h3>
<p><b>{{ summary }}</b></p>

<h3>📷 Image Details</h3>
<ul>
<li>File Name: {{ filename }}</li>
<li>File Size: {{ size }} KB</li>
<li>Dimensions: {{ dims }}</li>
</ul>

<h3>🔎 Raw Metadata</h3>
<pre>{{ metadata }}</pre>
</div>
{% endif %}

</body>
</html>
"""

def get_ai_summary(image_bytes):
    b64 = base64.b64encode(image_bytes).decode()

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "Describe what is happening in this image in one clear sentence."
                    },
                    {
                        "type": "input_image",
                        "image_base64": b64
                    }
                ],
            }
        ],
        max_output_tokens=150,
    )

    return response.output_text

@app.route("/", methods=["GET","POST"])
def home():
    summary = None
    metadata = ""
    filename = ""
    size_kb = ""
    dims = ""

    if request.method == "POST":
        file = request.files["image"]
        filename = file.filename

        img_bytes = file.read()
        temp_path = "temp.jpg"

        with open(temp_path, "wb") as f:
            f.write(img_bytes)

        # ---- Image info ----
        img = Image.open(temp_path)
        dims = f"{img.size[0]} x {img.size[1]}"
        size_kb = round(os.path.getsize(temp_path)/1024, 2)

        # ---- Metadata ----
        with open(temp_path, "rb") as f:
            tags = exifread.process_file(f)

        metadata = "\n".join([f"{k}: {v}" for k,v in tags.items()])

        # ---- AI Summary ----
        summary = get_ai_summary(img_bytes)

        os.remove(temp_path)

    return render_template_string(
        HTML,
        summary=summary,
        metadata=metadata,
        filename=filename,
        size=size_kb,
        dims=dims
    )

if __name__ == "__main__":
    app.run(debug=True)
