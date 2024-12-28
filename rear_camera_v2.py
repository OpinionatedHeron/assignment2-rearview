from sense_hat import SenseHat
import paho.mqtt.client as mqtt
from urllib.parse import urlparse
from datetime import datetime
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput
import threading #allowing the program to detect movement and record at the same time

#initialising senseHat
sense = SenseHat()

#path where videos are recorded to
VIDEO_PATH = "./videos/sensehat_video.h264"

# parse mqtt url for connection details
URL = urlparse("mqtt://broker.emqx.io:1883/opheron/home/cameras/cam1")
BASE_TOPIC = URL.path[1:]

# MQTT event callbacks
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected successfully")
    else:
        print(f"Connection failed with code {rc}")

def on_publish(client, userdata, mid):
    print(f"Message ID: {mid} published successfully")

def on_disconnect(client, userdata, rc):
    print("Disconnected from MQTT broker")
    if rc != 0:
        print("Unexpected disconnection. Reconnecting...")
        client.reconnect()

mqttc = mqtt.Client()

mqttc.on_connect = on_connect
mqttc.on_publish = on_publish

# check if userame and password in the url
if (URL.username):
    mqttc.username_pw_set(URL.username, URL.password)
# Connect
mqttc.connect(URL.hostname, URL.port)
mqttc.loop_start()

def publish_message():
    # Get the current time
    current_time = datetime.now()
   #Function to publish the message to the MQTT topic
    message = f"Video recorded at {current_time:%H:%M}"
    mqttc.publish(BASE_TOPIC, message)
    print("Message published:", message)

def record_video(output_file, duration):
    #Intialising the Picamera
    picam2 = Picamera2()

    #Configure camera for video recording
    video_config = picam2.create_video_configuration()
    picam2.configure(video_config)
    encoder = H264Encoder(10000000)
    output = FfmpegOutput(output_file)

    #Start recording
    picam2.start_recording(encoder, output)
    print("Recording video...")
    time.sleep(duration)
    picam2.stop_recording()
    picam2.close()
    print("Recording stopped...")
    publish_message()

#Check movement - camera should activate when moved backwards
def check_movement();
    global recording
    recording = False
    #getting previous acceleration to determine if it moves backwards
    past_accel = sense.get_accelerometer_raw()

    while True:
        current_accel = sense.get_accelerometer_raw()
        z_axis = current_accel['z']

        #Check if moving backwards
        if z_axis < -0.5 and not recording:
            recording = True
            record_video(VIDEO_PATH)

        #Check if moving forward
        elif z_axis > 0.5 and recording:
            recording = False
            print("Stopped recording - moving forward")

#Threading - allow recording and movement detection to run simultaneously
move_thread = threading.Thread(target=check_movement)
move_thread.start()

try:
    while True:
        time.sleep(1)
except ManualStop:
    print("Stop program")
    mqttc.loop_stop()