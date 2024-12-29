#Creating a streaming camera using code from https://picamera.readthedocs.io/
#Source: https://picamera.readthedocs.io/en/release-1.13/recipes2.html#web-streaming

import io
import cv2
import numpy as np
import logging
import socketserver
import time
import threading
from threading import Condition, Event
from http import server

from sense_hat import SenseHat
from BlynkLib import Blynk
from statistics import mean

from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput

#Initialize Blynk
BLYNK_AUTH = 'wCsvZULPg7-9L5mKwR9ZOEfwA_aV7qV3'
blynk = Blynk(BLYNK_AUTH)

#Initialize SenseHat
sense = SenseHat()

#Configure LEDs
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLANK = (0, 0, 0)

#Source: https://medium.com/@tauseefahmad12/object-detection-using-mobilenet-ssd-e75b177567ee 
#Initialize object detection
net = cv2.dnn.readNetFromCaffe('models/MobileNetSSD_deploy.prototxt', 
                               'models/MobileNetSSD_deploy.caffemodel')

#Gathered from source
#Dictionary model is trained on
classNames = { 0: 'background',
    1: 'aeroplane', 2: 'bicycle', 3: 'bird', 4: 'boat',
    5: 'bottle', 6: 'bus', 7: 'car', 8: 'cat', 9: 'chair',
    10: 'cow', 11: 'diningtable', 12: 'dog', 13: 'horse',
    14: 'motorbike', 15: 'person', 16: 'pottedplant',
    17: 'sheep', 18: 'sofa', 19: 'train', 20: 'tvmonitor'}

#Virtual pins for Blynk
MOVE_STATUS = 0
PROXIMITY_ALERT = 1
OBJECT_COUNT = 2
VIDEO_STATUS = 3
MOVEMENT = 4

#HTML to create streaming webpage
#Adding data from camera in case Blynk Fails
PAGE="""\
<html>
<head>
<title>Streaming - Rear View</title>
<script>
function updateStatusDisplay(elementId, value, isBoolean = false) {
    const element = document.getElementById(elementId);
    if (isBoolean) {
        element.textContent = value ? 'Yes' : 'No';
        element.className = 'status-value ' + (value ? 'active' : 'inactive');
    }else {
        element.textContent = value;
    }
}

function fetchDAta() {
    fetch('/data.json')
        .then(response => response.json())
        .then(data => {
            updateStatusDisplay('moveStatus', data.move_status, true);
            updateStatusDisplay('proximityAlert', data.proximity_alert, true);
            updateStatusDisplay('objectCount', data.object_count);
            updateStatusDisplay('videoStatus', 
                data.video_status, === 'Active' ? 'Active' : 'Standby',
                true);
            updateStatusDisplay('movement', 
                typeof data.movement === 'number' ? 
                data.movement.toFixed(2) : data.movement);
        })
        .catch(error => {
            console.error('Error fetching data:', error);
            document.querySelectorAll('.status-value').forEach(element => {
                element.textContent = 'Error loading data';
                element.className = 'status-value inactive';
            });
        });
}

document.addEventListener('DOMContentLoaded', () => {
    fetchData();
    setInterval(fetchData, 1000);
});
</script>
</head>
<body>
<h1>RPi - Testing Rearview & Motion Detection</h1>
<img src="rearview.mjpg" width="640" height="480" />
<h2>Rearview Camera Data</h2>
<ul>
    <li><strong>Move Status:</strong> <span id="moveStatus">Loading...</span></li>
    <li><strong>Proximity Alert:</strong> <span id="proximityAlert">Loading...</span></li>
    <li><strong>Object Count:</strong> <span id="objectCount">Loading...</span></li>
    <li><strong>Video Status:</strong> <span id="videoStatus">Loading...</span></li>
    <li><strong>Movement:</strong> <span id="movement">Loading...</span></li>
</ul>
</body>
</html>
"""
#Creating a separate page for when Blynk works and all data isn't required
SIMPLE_PAGE = """\
<html>
<head>
<title>Streaming - Rear View</title>
</head>
<body>
<h1>RPi - Rearview Camera Stream</h1>
<p>Blynk connection active - check your Blynk app for data</p>
<img src="rearview.mjpg" width="640" height="480" />
</body>
</html>
"""

class DetectMovement:
    def __init__(self, min_movement=0.05, num_readings=5, cooling_period=20):
        #Initialize accelerometer - which detects if RPi moves
        #Cooling_period - how long after movement stops that video keeps recording
        self.sense = SenseHat()
        self.min_movement = min_movement
        self.num_readings = num_readings
        self.cooling_period = cooling_period
        self.baseline = self.get_baseline()
        self.last_move_time = 0
        self.move_detected = Event()
        self.readings_buffer = []

        #Monitoring in separate thread
        self.running = True
        self.monitor_thread = threading.Thread(target=self.check_accelerometer, daemon=True)
        self.monitor_thread.start()

    #Get base reading when program starts
    def get_baseline(self):
        readings = []
        for _ in range(10): #10 readings to set baseline
            accel = self.sense.get_accelerometer_raw()
            magnitude = np.sqrt(accel['x']**2 + accel['y']**2 + accel['z']**2)
            readings.append(magnitude)
            time.sleep(0.1)
        return mean(readings) #average of gathered reading to set baseline
    
    #Monitor accelerometer data in sperarate thread
    def check_accelerometer(self):
        while self.running:
            accel = self.sense.get_accelerometer_raw()
            magnitude = np.sqrt(accel['x']**2 + accel['y']**2 + accel['z']**2)

            #Add readings to buffer
            self.readings_buffer.append(magnitude)
            if len(self.readings_buffer) > self.num_readings:
                self.readings_buffer.pop(0)
            
            avg_magnitude = mean(self.readings_buffer)

            if abs(avg_magnitude - self.baseline) > self.min_movement:
                self.last_move_time = time.time()
                self.move_detected.set()
            elif time.time() - self.last_move_time > self.cooling_period:
                self.move_detected.clear()

            blynk.virtual_write(MOVEMENT, avg_magnitude)

            time.sleep(0.1)

        #Check is device is moving
    def is_move_detected(self):
        return self.move_detected.is_set() or \
            (time.time() - self.last_move_time < self.cooling_period)
        
    def stop(self):
        self.running = False
        self.monitor_thread.join()


class VideoOutput(io.BufferedIOBase):
    def __init__(self, move_detector):
        self.frame = None
        self.condition = Condition()
        self.proximity_check = 0.2
        self.last_blynk_update = 0
        self.blynk_update_interval = 1
        self.move_detector = move_detector
        self.video_active = False
        self.current_frame = None

        #noticed a big delay with object detection
        #needed to improve frame processing
        self.frame_counter = 0
        self.process_every_n_frames = 3

    #Track Blynk status so the program still works if Blynk fails
        self.blynk_connected = True
        self.current_data = {
            'move_status': False,
            'proximity_alert': False,
            'object_count': 0,
            'video_status': 'Standby',
            'movement': 0.0
        }

        try:
            self.blynk = Blynk(BLYNK_AUTH)
            blynk_thread = threading.Thread(target=self.run_blynk, daemon=True)
            blynk_thread.start()
        except Exception as e:
            logging.error(f"Failed to initialize Blynk: {e}")
            self.blynk_connected = False

    def run_blynk(self):
        try:
            self.blynk.run()
        except Exception as e:
            logging.error(f"Failed to initialize Blynk: {e}")
            self.blynk_connected = False

    def update_data(self, detection_info, move_status):
        self.current_data.update({
            'move_status': move_status,
            'proximity_alert': detection_info.get('close_object', False),
            'object_count': detection_info.get('object_count', 0),
            'video_status': 'Active' if self.video_active else 'Standby',
            'movement': self.move_detector.readings_buffer[-1] if self.move_detector.readings_buffer else 0.0
        })

    #Update Blynk
    def update_blynk(self, detection_info, move_status):
        current_time = time.time()

        self.update_data(detection_info, move_status)

        if current_time - self.last_blynk_update >= self.blynk_update_interval:
            if self.blynk_connected:
                try:
                    self.blynk.virtual_write(MOVE_STATUS, 1 if move_status else 0)
                    self.blynk.virtual_write(VIDEO_STATUS, "Active" if self.video_active else "Standby")

                    if move_status:
                        self.blynk.virtual_write(PROXIMITY_ALERT, 1 if detection_info['close_object'] else 0)
                        self.blynk.virtual_write(OBJECT_COUNT, detection_info['object_count'])

                    self.last_blynk_update = current_time
                except Exception as e:
                    logging.error(f"Failed to initialize Blynk: {e}")
                    self.blynk_connected = False

    def write(self, buf):

        move_detected = self.move_detector.is_move_detected()

        if move_detected:
            frame = cv2.imdecode(np.frombuffer(buf, np.uint8), cv2.IMREAD_COLOR)
            self.frame_counter += 1

            if not self.video_active:
                self.video_active = True
                sense.clear(GREEN)

            if self.frame_counter % self.process_every_n_frames == 0:
                processed_frame = self.process_frame(frame, True)
            else:
                processed_frame = frame

            _, processed_buf = cv2.imencode('.jpg', processed_frame)

            with self.condition:
                self.frame = processed_buf.tobytes()
                self.current_frame = self.frame
                self.condition.notify_all()
        else:
            if self.video_active:
                self.video_active = False
                sense.clear(BLANK)

            with self.condition:
                self.frame = self.current_frame if self.current_frame else None
                self.condition.notify_all()


    def process_frame(self, frame, detect_objects=True):
        if not detect_objects:
            return frame
        
        #Preparing object detection
        (h,w) = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(frame, 0.007843, (300, 300), 127.5)

        #Initialize detection dictionary
        detection_info = {
            'close_object': False,
            'object_count': 0
        }

        #Run object detection
        net.setInput(blob)
        detection = net.forward()

        #Process objects detected in frame
        for i in range(detection.shape[2]):
            confidence = detection[0, 0, i, 2]

            if confidence > 0.5:
                detection_info['object_count'] += 1

                class_id = int(detection[0, 0, i, 1])
                class_name = classNames[class_id]

                box = detection[0, 0, i, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype("int")

                object_size = ((endX - startX) * (endY - startY)) / (w * h)

                if object_size > self.proximity_check:
                    detection_info['close_object'] = True

                cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 255, 0), 2)
                label = f"{class_name}: {confidence * 100:.2f}%"

                y = startY - 10 if startY - 10 > 10 else startY + 10
                cv2.putText(frame, label, (startX, y), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        if detection_info['close_object']:
            sense.clear(RED)
        else:
            sense.clear(GREEN)

        self.update_blynk(detection_info, True)

        return frame

class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':

            if not output.blynk_connected:
                content = PAGE.encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.send_header('Content-Length', len(content))
                self.end_headers()
                self.wfile.write(content)
            else:
                content = SIMPLE_PAGE.encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.send_header('Content-Length', len(content))
                self.end_headers()
                self.wfile.write(content)

        elif self.path == '/rearview.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))

        elif self.path == '/data.json':
            if not output.blynk_connected:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(output.current_data).encode('utf-8'))
            else:
                self.send_error(503)
                self.end_headers()
        elif self.path == '/rearview.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

def main():
    move_detector = DetectMovement(
        min_movement=0.05,
        num_readings=5,
        cooling_period=20
    )

    global output

    picam2 = Picamera2()
    picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
    output = VideoOutput(move_detector)

    picam2.start_recording(JpegEncoder(), FileOutput(output))
    sense.clear(BLANK)

    blynk_thread = threading.Thread(target=blynk.run, daemon=True)
    blynk_thread.start()

    try:
        address = ('', 5000)
        server = StreamingServer(address, StreamingHandler)
        server.serve_forever()
    finally:
        picam2.stop_recording()
        move_detector.stop()
        sense.clear()

if __name__ == '__main__':
    main()