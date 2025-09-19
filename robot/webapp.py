import cv2
import time
import threading
import logging
from flask import Flask, render_template_string, request, jsonify, Response
from pyzbar import pyzbar
from picar import Picar

app = Flask(__name__)

OFFSET = 20

# Global variables and constants
OFFSET = 0  # Adjust as needed for servo calibration
lock = threading.Lock()
current_qr = None
camera_instance = None
camera_lock = threading.Lock()
picar_instance = None

# Initialize PiCar (singleton pattern)
def get_picar():
    global picar_instance
    if picar_instance is None:
        try:
            picar_instance = Picar()
            logging.info("PiCar initialized successfully")
        except Exception as e:
            logging.error(f"Error initializing PiCar: {e}")
            picar_instance = None
    return picar_instance

# Initialize Picamera2 (singleton pattern)
def get_camera():
    global camera_instance
    with camera_lock:
        if camera_instance is None:
            try:
                from picamera2 import Picamera2
                picam2 = Picamera2()
                config = picam2.create_video_configuration(main={"size": (1280, 720), "format": "RGB888"})
                picam2.configure(config)
                picam2.start()
                camera_instance = picam2
                logging.info("Picamera2 initialized successfully")
            except ImportError:
                logging.error("Picamera2 not available, using OpenCV camera")
                camera_instance = cv2.VideoCapture(0)
            except Exception as e:
                logging.error(f"Error initializing Picamera2: {e}, falling back to OpenCV")
                camera_instance = cv2.VideoCapture(0)
        return camera_instance

def scan_for_qr_at_position(camera, angle):
    """Scan for QR code at a specific camera angle"""
    picar = get_picar()
    if picar:
        picar.set_camera_angle(angle)
        time.sleep(1)  # Wait for servo to move
    
    # Capture a frame for QR scanning
    if hasattr(camera, 'capture_array'):
        # Picamera2
        frame = camera.capture_array()
    else:
        # OpenCV VideoCapture
        ret, frame = camera.read()
        if not ret:
            return None
    
    if frame is None:
        return None
    
    # Convert to grayscale for QR detection
    if len(frame.shape) == 3:
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY if hasattr(camera, 'capture_array') else cv2.COLOR_BGR2GRAY)
    else:
        gray = frame
        
    # Detect QR codes
    qr_codes = pyzbar.decode(gray)
    
    if qr_codes:
        # Get the first QR code found
        qr_data = qr_codes[0].data.decode('utf-8')
        logging.info(f"QR code detected at angle {angle}°: {qr_data}")
        return qr_data
    
    return None

def perform_scan_sequence():
    """Perform the complete scanning sequence: left -> center -> right, up to 3 cycles"""
    global current_qr
    camera = get_camera()
    picar = get_picar()
    
    if not camera:
        return {'qr': None, 'error': 'Camera not available'}

    scan_positions = [-45 + OFFSET, 0 + OFFSET, 45 + OFFSET]  # Left 45°, Center, Right 45°
    max_cycles = 3
    
    for cycle in range(max_cycles):
        logging.info(f"Starting scan cycle {cycle + 1}/{max_cycles}")
        
        for angle in scan_positions:
            logging.info(f"Scanning at {angle}° (cycle {cycle + 1})")
            qr_data = scan_for_qr_at_position(camera, angle)
            
            if qr_data:
                # QR code found, update global variable and return immediately
                with lock:
                    current_qr = qr_data
                
                # Return camera to center position
                if picar:
                    picar.set_camera_angle(0)
                
                logging.info(f"QR code scan complete: {qr_data}")
                return {'qr': qr_data}
        
        # Small delay between cycles
        time.sleep(0.1)
    
    # No QR code found after all cycles
    logging.warning("No QR code detected after 3 complete scan cycles")
    with lock:
        current_qr = None
    
    # Return camera to center position
    if picar:
        picar.set_camera_angle(0)
    
    return {'qr': None}

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
<style>
    .container { max-width: 800px; margin: auto; padding: 20px; background: #f9f9f9; border-radius: 8px; box-shadow: 0 2px 8px #ccc; }
    h1 { text-align: center; }
    #video { display: block; margin: 0 auto 16px auto; border-radius: 4px; box-shadow: 0 1px 4px #aaa; }
    #scan-btn { display: block; margin: 16px auto; padding: 10px 24px; font-size: 1.1em; background: #007bff; color: #fff; border: none; border-radius: 4px; cursor: pointer; transition: background 0.2s; }
    #scan-btn:hover { background: #0056b3; }
    #status { text-align: center; color: #888; margin-bottom: 8px; }
    #qr-container { text-align: center; font-size: 1.2em; margin-top: 12px; padding: 8px; border-radius: 4px; background: #e9ecef; display: inline-block; min-width: 200px; }
    #qr-container.flash { background: #ffe066; transition: background 0.3s; }
</style>
</head>
<body>
<div class='container'>
    <h1>PiCar Camera Stream</h1>
    <img id='video' src='/video_feed' width='720' height='405'>
    <button id='scan-btn'>Start Scan</button>
    <div id='status'></div>
    <h2 style='text-align:center;'>Current QR Code</h2>
    <div id='qr-container'><span id='qr-code'></span></div>
</div>
<script>
let lastQR = null;
const scanBtn = document.getElementById('scan-btn');
const qrSpan = document.getElementById('qr-code');
const qrContainer = document.getElementById('qr-container');
const statusDiv = document.getElementById('status');

function fetchCurrentQR() {
    fetch('/qr_code')
        .then(response => response.json())
        .then(data => {
            if (data.qr) {
                qrSpan.textContent = data.qr;
                if (data.qr !== lastQR) {
                    qrContainer.classList.add('flash');
                    setTimeout(() => qrContainer.classList.remove('flash'), 300);
                }
            } else {
                qrSpan.textContent = '';
                qrContainer.classList.remove('flash');
            }
            lastQR = data.qr;
        });
}

function startScan() {
    statusDiv.textContent = 'Scanning...';
    fetch('/start_scan', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.qr) {
                qrSpan.textContent = data.qr;
                qrContainer.classList.add('flash');
                setTimeout(() => qrContainer.classList.remove('flash'), 300);
                statusDiv.textContent = 'Scan complete.';
            } else {
                qrSpan.textContent = '';
                statusDiv.textContent = 'No QR code detected.';
            }
            lastQR = data.qr;
        })
        .catch(() => {
            statusDiv.textContent = 'Scan failed.';
        });
}

scanBtn.addEventListener('click', startScan);
setInterval(fetchCurrentQR, 2000);
window.onload = fetchCurrentQR;
</script>
</body>
</html>
"""

def gen_frames():
    camera = get_camera()
    
    while True:
        try:
            # Check if using Picamera2 or OpenCV
            if hasattr(camera, 'capture_array'):
                # Picamera2
                frame = camera.capture_array()
            else:
                # OpenCV VideoCapture
                ret, frame = camera.read()
                if not ret:
                    time.sleep(0.1)
                    continue
            
            if frame is None:
                time.sleep(0.1)
                continue
                
            # Picamera2 gives RGB, OpenCV gives BGR
            if hasattr(camera, 'capture_array'):
                # Picamera2 - convert RGB to BGR for cv2.imencode
                bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            else:
                # OpenCV - already in BGR
                bgr_frame = frame
                
            ret, jpeg = cv2.imencode('.jpg', bgr_frame)
            if not ret:
                time.sleep(0.1)
                continue
                
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
            time.sleep(0.1)
            
        except Exception as e:
            logging.error(f"Error in frame generation: {e}")
            time.sleep(1)

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/qr_code')
def qr_code():
    with lock:
        qr = current_qr
    return jsonify({'qr': qr})

@app.route('/start_scan', methods=['POST'])
def start_scan():
    try:
        logging.info("Starting QR code scan sequence")
        result = perform_scan_sequence()
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Error in start_scan: {e}")
        return jsonify({'qr': None, 'error': str(e)})

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def cleanup_camera():
    global camera_instance
    with camera_lock:
        if camera_instance is not None:
            try:
                if hasattr(camera_instance, 'stop'):
                    camera_instance.stop()
                elif hasattr(camera_instance, 'release'):
                    camera_instance.release()
            except Exception as e:
                logging.error(f"Error cleaning up camera: {e}")
            finally:
                camera_instance = None

def cleanup_picar():
    global picar_instance
    if picar_instance is not None:
        try:
            picar_instance.set_camera_angle(0)  # Return to center
            picar_instance.exit()
        except Exception as e:
            logging.error(f"Error cleaning up PiCar: {e}")
        finally:
            picar_instance = None

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
    finally:
        cleanup_camera()
        cleanup_picar()
