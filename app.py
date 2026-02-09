
from flask import Flask, request, render_template_string
from PIL import Image
import exifread, os, requests, base64
from openai import OpenAI

app = Flask,(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Smart Image Analyzer</title>
</head>
<body>
<h2>Upload Image</h2>
<form method="post" enctype="multipart/form-data">
<input type="file" name="image" required>
<button type="submit">Analyze</button>
</form>

{% if summary %}
<h3>AI Summary:</h3>
<p>{{ summary }}</p>

<h3>Metadata:</h3>
<pre>{{ metadata }}</pre>
{% endif %}
</body>
</html>
"""

def analyze_image_with_ai(image_path):
    with open(image_path, "rb") as img:
        base64_image = base64.b64encode(img.read()).decode("utf-8")

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe what is happening in this image in one clear sentence."},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                    },
                ],
            }
        ],
    )
    return response.choices[0].message.content

@app.route("/", methods=["GET","POST"])
def upload():
    summary = None
    metadata = None

    if request.method == "POST":
        file = request.files["image"]
        path = "temp.jpg"
        file.save(path)

        with open(path, "rb") as f:
            tags = exifread.process_file(f)

        meta_list = [f"{tag}: {tags[tag]}" for tag in tags]

        # AI Image description
        summary = analyze_image_with_ai(path)

        metadata = "\n".join(meta_list)

        os.remove(path)

    return render_template_string(HTML, summary=summary, metadata=metadata)

if __name__ == "__main__":
    app.run(debug=True)
