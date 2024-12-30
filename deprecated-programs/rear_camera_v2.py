#Test - Old Version - not using

from sense_hat import SenseHat
from flask import Flask, request, send_file
from flask_cors import CORS
from datetime import datetime
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput
import threading #allowing the program to detect movement and record at the same time
import time

#initialising senseHat
sense = SenseHat()
sense.clear()

#path where videos are recorded to
VIDEO_PATH = "./videos/"
#Locks thread, so they occur in the correct order
lock = threading.Lock()
recording = False

#creating Flask app and apply CORS
app = Flask(__name__)
CORS(app)

#Intialising the Picamera
picam2 = Picamera2()
#Configure camera for video recording
video_config = picam2.create_video_configuration()
picam2.configure(video_config)
encoder = H264Encoder(10000000)

def publish_message():
    #Get the current time
    current_time = datetime.now()
    #Function to publish the message to the MQTT topic
    message = f"Video recorded at {current_time:%H:%M}"
    
    print("Message published:", message)

def record_video(output_file):
    global recording
    with lock:
        recording = True
    try:
        #Start recording
        picam2.start_recording(encoder, FfmpegOutput(output_file))
        print("Recording video...")
        time.sleep(180) #Recording for 3 minutes to have enough time
    finally:
        picam2.stop_recording()
        print("Recording stopped...")
        publish_message()
        with lock:
            recording = False

#Check movement - camera should activate when moved backwards
def check_movement():
    global recording

    while True:
        current_accel = sense.get_accelerometer_raw()
        z_axis = current_accel['z']
        with lock:
            #Check if moving backwards
            if z_axis < -0.5 and not recording:
                video_file = f"{VIDEO_PATH}sensehat_video{datetime.now():%Y%m%d_%H%M%S}.h264"
                threading.Thread(target=record_video, args=(video_file,)).start()

            #Check if moving forward
            elif z_axis > 0.5 and recording:
                print("Stopped recording - moving forward")

#Threading - allow recording and movement detection to run simultaneously
move_thread = threading.Thread(target=check_movement, daemon=True)
move_thread.start()

#Create web API Path to Resource 
@app.route('/video_feed', methods=['GET'])
def video_feed():
    return send_file(f"{VIDEO_PATH}sensehat_video.h264", mimetype='video/h264')

#Run API on port 5000, set debug to true
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
