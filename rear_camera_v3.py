#Creating a streaming camera using code from https://picamera.readthedocs.io/
#Source: https://picamera.readthedocs.io/en/release-1.13/recipes2.html#web-streaming

import io
import cv2
import numpy as np
import logging
import socketserver
import time
import threading
from threading import Condition
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
MOVE_STATUS

#HTML to create streaming webpage
PAGE="""\
<html>
<head>
<title>Streaming - Rear View</title>
</head>
<body>
<h1>RPi - Testing Rearview & Motion Detection</h1>
<img src="rearview.mjpg" width="640" height="480" />
</body>
</html>
"""

class DetectMovement:
    def __init__(self, min_movement=0.2, num_readings=3, cooling_period=20):
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
        self.monitor_thread = threading.Thread(target=self.monitor_movement, daemon=True)
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

            blynk.virtual_write(MOVE_PIN, avg_magnitude)

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
        self.proximity_check = 1
        self.last_blynk_update = 0
        self.blynk_update_interval = 1
        self.move_detector = move_detector
        self.video_active = False

    #Update Blynk
    def update_blynk(self, detection_info, move_status):
        current_time = time.time()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()

class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
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
        else:
            self.send_error(404)
            self.end_headers()


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
output = StreamingOutput()
picam2.start_recording(JpegEncoder(), FileOutput(output))

try:
    address = ('', 5000)
    server = StreamingServer(address, StreamingHandler)
    server.serve_forever()
finally:
    picam2.stop_recording()