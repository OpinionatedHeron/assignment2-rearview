import BlynkLib
import time
import cv2
from sense_hat import SenseHat
from picamera2 import Picamera2
from flask import Flask, Response

#initialise SenseHAT
sense = SenseHat()
sense.clear()

#Blynk authentication token
BLYNK_AUTH = 'wCsvZULPg7-9L5mKwR9ZOEfwA_aV7qV3'

#Initialise Blynk instance
blynk = BlynkLib.Blynk(BLYNK_AUTH)

GLITCH_API_URL = "https://rearview-camera.glitch.me/upload"

REVERSE = -1.0 #Setting backward movement detection
FORWARD = 1.0 #Setting forward movement detection

#Tracks if the camera is recording or not
is_recording = FALSE


try:
    while True:
        #get acceleration reading
        acceleration = sense.get_accelerometer_raw()
        z_axis = acceleration['z'] #z axiz is when RPi is flat, not rotated

        if z_axis < REVERSE and not is_recording:
            print("Recording now...")
            camera.start_recording('motion_video.h264')
            is_recording = True
            time.sleep(0.1)

        elif z_axis > FORWARD and is_recording:
            print("End recording...")
            camera.stop_recording()
            is_recording = False
            time.sleep(0.1)

        time.sleep(0.1)

except ManualStop:
    if is_recording:
        camera.stop_recording()
    print("End recording...")

finally:
    camera.close()