"""
Web server for streaming camera images and logging detected QR codes.
Organized and readable code using Flask and threading.
"""

from flask import Flask, Response, render_template_string
from picamera2 import Picamera2
from pyzbar import pyzbar
import threading
import time
import cv2
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

# Flask app setup
app = Flask(__name__)

# Camera setup
RESOLUTION = (640, 480)
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"size": RESOLUTION}))
picam2.start()

# Shared state for QR code log
detected_qrcodes = []
lock = threading.Lock()

# HTML template for web page
HTML_PAGE = """
<!doctype html>
<title>PiCar Camera Stream</title>
<h1>Live Camera Stream</h1>
<img src="/video_feed" width="640" height="480">
<h2>Detected QR Codes</h2>
<ul>
{% for code in codes %}
  <li>{{ code }}</li>
{% endfor %}
</ul>
"""

def gen_frames():
    """Generator for streaming camera frames as JPEG."""
    while True:
        frame = picam2.capture_array()
        # Detect QR codes
        qr_codes = pyzbar.decode(frame)
        with lock:
            for qr in qr_codes:
                data = qr.data.decode('utf-8')
                if data not in detected_qrcodes:
                    detected_qrcodes.append(data)
                    logging.info(f"Detected QR code: {data}")
        # Encode frame as JPEG
        ret, jpeg = cv2.imencode('.jpg', frame)
        if not ret:
            continue
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
        time.sleep(0.1)

@app.route('/')
def index():
    with lock:
        codes = list(detected_qrcodes)
    return render_template_string(HTML_PAGE, codes=codes)

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
