# Assignment 2 - Rearview Camera

The goal of this assignment was to create a rearview camera which could assist drivers when reversing their vehicle. I decided to create this type of device as my own car is an older model and has no reverse assistance. The camera begins recording when the device moves. While recording, it detects and identifies any objects within the frame, if an object takes up a certain percentage of the frame is creates a proximity alert for the driver.

## Installation

This program is written using Python and some HTML, it can be downloaded and used on a Raspberry Pi or similar device. If using a Raspberry Pi, I recommend the 4B Model with an attached SenseHAT and a Raspberry Pi Camera as this is the hardware that I used.

In order to ensure that this program runs on your device, you must ensure that it is set up correctly with all of the relevant libraries installed.

### Set Up Raspberry Pi	
1. Install Raspberry Pi OS onto a microSD card – ensure that you set a hostname, username and password
2. While the device is off (and unplugged), insert the microSD and boot up the device. Once the device is active, find Raspberry Pi using:
```bash
nmap -sn <Network> 
```
If you have trouble finding your device IP Address, you can ping the hostname of your device to see if it is on your network
```bash
ping <hostname>
```
3. Once the device is active, access it's Secure Shell (SSH) Protocol to securely send commands to your device. You can access SSH with the following command - replace user, Ip address, and hostname with your own information:
```bash
ssh user@ipaddress/hostname
```
4. Check that your Raspberry Pi is up to date with before installing any additional libraries.
```bash
sudo apt-get update
sudo apt-get upgrade
```
5. Now we can install all the libraries necessary to run this program. Start with installing SenseHAT -
```bash
sudo apt-get install sense-hat 
```
This will allow us to use the accelerometer within the SenseHAT to act as our motion detection for the camera activation.
6. Next, install the Pi Camera. For this, we need the picamera library, as well as OpenCV to ensure the camera functions as required.
```bash
sudo apt install python3-picamera
sudo pip3 install opencv-python 
```
7. Numpy is used so that the program can work with arrays. These are used when dealing with the coordinates needed to detect movement and relevant objects.
```bash
sudo pip3 install numpy 
```
8. Lastly, we need to install Blynk. This was the library I had the most trouble getting installed, as the general installation only installed older versions of the library, which does not run with our program. The most effective workaround I have found is the following:
```bash
pip install git+https://github.com/vshymanskyy/blynk-library-python 
```
9. With this, your Raspberry Pi should be correctly set up to run the rearview program.

## Usage
Start running the program using:
```bash
python rear_camera_v3.py
```
When it runs effectively you should be able to watch the stream through the webpage (http://<deviceIPaddress>:5000).

![image](https://github.com/user-attachments/assets/f30b020c-39c0-4b3d-8e6c-8b3f6882c2c2)

If BLYNK functions correctly, you should be able to check your data in the device dashboard.

![Screenshot 2024-12-30 220238](https://github.com/user-attachments/assets/42f8ebf2-f69c-4cc7-ad06-814e1d57f683)

If BLYNK fails, then the data should be visible on the same webpage that streams the video. 

While the device is in motion and there are objects detected in frame, the LEDs should flash green. If an object gets too close to the camera (i.e. it takes up a certain percentage of the frame) this will set off the proximity alert and the LEDs should flash red.

## Support
The following YouTube videos can help with getting you started:
- Cytron Technologies: Blynk Video Streaming Using Raspberry Pi Camera - https://youtu.be/34qj3b6AK4w?si=ovuPhCofETI3dnl2
- Ethan's Pi Tips: Autonomous Driving Object Detection on the Raspberry Pi 4! - https://youtu.be/Zfmo3bMycUg?si=_a3XCWCqfTQIRXFd
- Damien Murtagh: Sense Hat identifying movement - https://youtu.be/hm0en0ribls?si=vzl_3pK5ugII8F9s

## Used Sources & Additional Resources
### Previous Rearview Examples
- RPi Backup Camera: https://github.com/caseymorris61/rpi_backup_camera
- RPi Backup Camera: https://caseytmorris.com/blog/2019/10/31/rpi-backup-camera/
- Pi zero w for car rear view backup camera: https://www.reddit.com/r/RASPBERRY_PI_PROJECTS/comments/xx4rld/pi_zero_w_for_car_rear_view_backup_camera/
- RearPi - Use your Raspberry Pi as Rear View / Backup Camera and Dashcam: https://forums.raspberrypi.com/viewtopic.php?t=181861

### Video Streaming
- PiCamera2 Manual: chrome-extension://efaidnbmnnnibpcajpcglclefindmkaj/https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf
- Using Picamera2 With Cv2 / OpenCv: https://forums.raspberrypi.com/viewtopic.php?t=369522
- Blynk Video Streaming Using Raspberry Pi Camera: https://www.cytron.io/tutorial/blynk-video-streaming-using-raspberry-pi-camera
- Blynk Video Widget: https://docs.blynk.io/en/blynk.console/widgets-console/video
- Video Streaming with Raspberry Pi Camera: https://randomnerdtutorials.com/video-streaming-with-raspberry-pi-camera/
- Raspberry Pi: MJPEG Streaming Web Server (Picamera2): https://randomnerdtutorials.com/raspberry-pi-mjpeg-streaming-web-server-picamera2/
-  How to stream a capture video using Picamera2: https://stackoverflow.com/questions/74131698/how-to-stream-a-capture-video-using-picamera2
- Picamera2 output to file and stream: https://forums.raspberrypi.com/viewtopic.php?t=354272
- Raspberry Pi Python Picamera2 Motion Detection Camera Frame Rate: https://forums.raspberrypi.com/viewtopic.php?t=346251
- Web streaming: https://picamera.readthedocs.io/en/release-1.13/recipes2.html#web-streaming
- PiCamera2 OpenCV Face Detect: https://github.com/raspberrypi/picamera2/blob/main/examples/opencv_face_detect_3.py

### SenseHAT
- SenseHAT About: https://www.raspberrypi.com/documentation/accessories/sense-hat.html#:~:text=The%20Raspberry%20Pi%20Sense%20HAT,colour%2C%20orientation%2C%20and%20movement.
- Getting started with the Sense HAT: https://projects.raspberrypi.org/en/projects/getting-started-with-the-sense-hat/8
- Accelerometer: https://activityworkshop.net/electronics/raspberrypi/accelerometer.html

### Object Detection
- Object Detection using mobilenet SSD: https://medium.com/@tauseefahmad12/object-detection-using-mobilenet-ssd-e75b177567ee
- How to Perform Object Detection with TensorFlow Lite on Raspberry Pi: https://www.digikey.ie/en/maker/projects/how-to-perform-object-detection-with-tensorflow-lite-on-raspberry-pi/b929e1519c7c43d5b2c6f89984883588
- Object and Animal Recognition With Raspberry Pi and OpenCV: https://core-electronics.com.au/guides/object-identify-raspberry-pi/
- TensorFlow-Object-Detection-on-the-Raspberry-Pi: https://github.com/EdjeElectronics/TensorFlow-Object-Detection-on-the-Raspberry-Pi
- rpi_road_object_detection: https://github.com/ecd1012/rpi_road_object_detection

### Additional Resources
- Installing NumPy: https://numpy.org/install/
- Why Use NumPy?: https://www.w3schools.com/python/numpy/numpy_intro.asp
- An Intro to Threading in Python: https://realpython.com/intro-to-python-threading/
- Multithreading in Python: https://www.geeksforgeeks.org/multithreading-python-set-1/

## Contribute
Contributions and improvements are always welcome!
