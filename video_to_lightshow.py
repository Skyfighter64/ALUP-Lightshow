import numpy as np
import cv2

import sys
import os
import time
from pyalup.Frame import Frame 

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from lightshow.lightshow import Lightshow

"""

Simple script turning a mp4 video file into a lightshow JSON which can be used with lightshow.py
Scales the given video down to one horizontal line of NUM_LED pixels. Only works for a single device.

"""

 
# the Number of LEDs
NUM_LEDS = 100
VIDEO_PATH = r"video.mp4"
output_path = "lightshow.json"

def main():
    cap = cv2.VideoCapture(VIDEO_PATH)
    show = Lightshow()
    show.frames = [[]] # initialize frames for one device
    while cap.isOpened():

        # NOTE: We need to get it BEFORE reading the actual frame to be correct
        # get the time stamp of the current video frame in ms
        timestamp = int(cap.get(cv2.CAP_PROP_POS_MSEC))

        ret, frame = cap.read()
        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            break
        
        #cv2.imshow('frame', frame)



        # rescale frame to n x 1 resolution
        resized_frame = cv2.resize(frame, (NUM_LEDS,1))

        AddFrameToLightshow(show, list(resized_frame)[0], timestamp)

        #cv2.imshow('frame', resized_frame)
        #print(f"Resized frame: {timestamp}ms")
        #print(resized_frame)

        reresized_frame = cv2.resize(resized_frame, None, fx=25, fy = 25)
        cv2.imshow('frame', reresized_frame)

        if cv2.waitKey(1) == ord('q'):
            break
    
    # close all cv2 related stuff
    cap.release()
    cv2.destroyAllWindows()

    # export the lightshow as json
    show.toJson(output_path)



# add a frame with the given colors and the given time stamp
# to the given lightshow
# @param lightshow: a lightshow object
# @param colors: an array of hexadecimal RGB values
# @param timestamps: the time stamp in ms of the given frame
def AddFrameToLightshow(lightshow, colors, timestamp):
    frame = Frame()
    frame.colors = [rgbToHex(r,g,b) for (r,g,b) in colors]
    frame.timestamp = timestamp
    # NOTE: currently, this will only work for one single device
    lightshow.frames[0].append(frame)


def rgbToHex(r,g,b):
    return "0x{0:02x}{1:02x}{2:02x}".format(clamp(r), clamp(g), clamp(b))

def clamp(x): 
  return max(0, min(x, 255))


if __name__ == "__main__":
    main()