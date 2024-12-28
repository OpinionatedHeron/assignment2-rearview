import BlynkLib
import cv2
from sense_hat import SenseHat
from picamera2 import Picamera2
from flask import Flask, Response

#initialise SenseHAT
sense = SenseHat()

#Blynk authentication token
BLYNK_AUTH = 'wCsvZULPg7-9L5mKwR9ZOEfwA_aV7qV3'

#Initialise Blynk instance
blynk = BlynkLib.Blynk(BLYNK_AUTH)