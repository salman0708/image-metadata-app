
import os, base64, exifread
from flask import Flask, request, render_template_string
from PIL import Image
from openai import OpenAI

app = Flask(__name__)

# Read API key from environment variable
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>AI Image Summary</title>
</head>
<body>
<h2>Upload Image</h2>

<form method="post" enctype="multipart/form-data">
<input type="file" name="image" required>
<button type="submit">Analyze</button>
</form>

{% if summary %}
<h3>AI Image Summary:</h3>
<p><b>{{ summary }}</b></p>

<h3>Metadata:</h3>
<pre>{{ metadata }}</pre>
{% endif %}
</body>
</html>
"""

def get_image_summary(image_path):
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text",
                     "text": "Describe what is happening in this image in one clear sentence."},
                    {
                        "type": "input_image",
                        "image_base64": b64,
                    },
                ],
            }
        ],
        max_output_tokens=150,
    )

    return response.output_text

@app.route("/", methods=["GET","POST"])
def upload():
    summary = None
    metadata = None

    if request.method == "POST":
        file = request.files["image"]
        path = "temp.jpg"
        file.save(path)

        # ---- Read metadata ----
        with open(path, "rb") as f:
            tags = exifread.process_file(f)

        meta_list = [f"{tag}: {tags[tag]}" for tag in tags]
        metadata = "\n".join(meta_list)

        # ---- Get AI summary ----
        summary = get_image_summary(path)

        os.remove(path)

    return render_template_string(HTML, summary=summary, metadata=metadata)

if __name__ == "__main__":
    app.run(debug=True)
