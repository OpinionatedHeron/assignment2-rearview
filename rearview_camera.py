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

REVERSE = -1.0 #Setting backward movement detection
FORWARD = 1.0 #Setting forward movement detection

#Tracks if the camera is recording or not
is_recording = FALSE

@blynk.on("V1")
try:
    while True:
            #get acceleration reading
            acceleration = sense.get_accelerometer_raw()
            z_axis = acceleration['z'] #z axiz is when RPi is flat, not rotated

            if z_axis < REVERSE:
                    camera.start_recording('motion_video.h264')