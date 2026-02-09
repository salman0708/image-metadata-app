from flask import Flask, request, render_template_string
from PIL import Image
import exifread
import os
import requests

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Image Metadata Analyzer</title>
</head>
<body>
    <h2>Upload an Image to Analyze Metadata</h2>
    <form method="post" enctype="multipart/form-data">
        <input type="file" name="image" required>
        <button type="submit">Analyze</button>
    </form>

    {% if result %}
    <h3>Metadata Summary:</h3>
    <pre>{{ result }}</pre>
    {% endif %}
</body>
</html>
"""

def get_location(lat, lon):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
        headers = {"User-Agent": "MetadataApp"}
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        return data.get("display_name", "Location not found")
    except:
        return "Location lookup failed"

@app.route("/", methods=["GET", "POST"])
def upload():
    result = None

    if request.method == "POST":
        file = request.files["image"]
        path = "temp.jpg"
        file.save(path)

        img = Image.open(path)
        size = os.path.getsize(path)

        with open(path, "rb") as f:
            tags = exifread.process_file(f)

        meta = []
        gps_lat = gps_lon = None

        for tag in tags:
            if "GPSLatitude" in tag:
                gps_lat = tags[tag]
            if "GPSLongitude" in tag:
                gps_lon = tags[tag]
            meta.append(f"{tag}: {tags[tag]}")

        location = "Not available"
        if gps_lat and gps_lon:
            lat = str(gps_lat)
            lon = str(gps_lon)
            location = get_location(lat, lon)

        result = f"""
File Name: {file.filename}
File Size: {size/1024:.2f} KB
Dimensions: {img.size[0]} x {img.size[1]}

Detected Metadata:
------------------
{chr(10).join(meta)}

Estimated Location:
{location}
"""

        os.remove(path)

    return render_template_string(HTML, result=result)

if __name__ == "__main__":
    app.run(debug=True)
