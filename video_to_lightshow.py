import numpy as np
import cv2

import sys
import os
import time
import logging
import argparse
from pyalup.Frame import Frame 

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from lightshow.lightshow import Lightshow
from lightshow.arrangement import Arrangement

"""

Simple script turning a mp4 video file into a lightshow JSON which can be used with lightshow.py
Scales the given video down to one horizontal line of NUM_LED pixels. Only works for a single device.

"""
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

parser = argparse.ArgumentParser(prog="Video To Lightshow", description="Convert video files to ALUP light shows which can be played with the light show player")
# setup arg parser
parser.add_argument('video_file', help="Specify a video file to create a lightshow from")
parser.add_argument('-n', '--num_leds', default=100, type=int, help="The number of LEDs of the LED strip. Will define the number of colors inside each frame.")      # option that takes a value
parser.add_argument('-o', '--output', default='output.json', help="The output json file to which the light show will be written. Default: 'output.json'")      # option that takes a value
parser.add_argument('-v', '--verbose', action='store_true', help="Enable verbose logging")  # on/off flag
parser.add_argument('--suppress_live_view', action='store_true', help="Disable the live viewing window")
parser.add_argument('-a','--arrangement', default='arrangements/linear.bmp', help="Specify a bitmap with the positions of the LEDs. The integer color value of each pixel represents the LEDs index. White (0xffffff) pixels are ignored")

def main():
    # handle cmdline args
    args = parser.parse_args()

    if(args.verbose):
        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)


    # read in LED arrangement
    logger.info("Generating arrangement from bitmap " + str(args.arrangement))
    arrangement = Arrangement()
    arrangement.FromBitmap(args.arrangement)
    #arrangement, arrangement_shape = ArrangementFromBitmap(args.arrangement)

    mask = arrangement.GetMask()

    #logger.debug("Mask" + str(mask))  
    cap = cv2.VideoCapture(args.video_file)
    show = Lightshow()
    show.frames = [[]] # initialize frames for one device

    logger.info("Converting video...")
    while cap.isOpened():

        # NOTE: We need to get it BEFORE reading the actual frame to be correct
        # get the time stamp of the current video frame in ms
        timestamp = int(cap.get(cv2.CAP_PROP_POS_MSEC))

        ret, frame = cap.read()
        if not ret:
            logger.info("Video end reached.")
            break


        # rescale frame to the same resolution as the arrangement
        resized_frame = cv2.resize(frame, arrangement_shape)
        resized_frame = cv2.bitwise_and(resized_frame, mask)

        # sample from the frame based on the LED positions defined in the arrangement
        colors = SampleFromFrame(resized_frame, arrangement)

        # add the colors of this frame to the light show
        AddFrameToLightshow(show, colors, timestamp)

        # provide a live view of what's currently processed
        if not args.suppress_live_view:
            reresized_frame = cv2.resize(resized_frame, None, fx=25, fy = 25, interpolation = cv2.INTER_NEAREST)
            cv2.imshow('frame', reresized_frame)

            # show the raw color output for debug purposes
            if (logger.level <= logging.DEBUG):
                cv2.imshow("colors", cv2.resize(cv2.cvtColor(np.array([colors]), cv2.COLOR_RGB2BGR), None, fx=25, fy = 25, interpolation = cv2.INTER_NEAREST))

        if cv2.waitKey(1) == ord('q'):
            break
    
    # close all cv2 related stuff
    cap.release()
    cv2.destroyAllWindows()
    logger.info("Converting to JSON")
    # export the lightshow as json
    show.toJson(args.output)
    logger.info("Done. Saved to " + str(args.output))


# sample from a frame using the given arrangement tuples (index, x, y)
def SampleFromFrame(frame, arrangement):
    rgb_frame =  cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    colors = [None for _ in range(len(arrangement.coordinates))]
    for led in arrangement.coordinates:
        index = led[0]
        x = led[1]
        y = led[2]
        colors[index] = rgb_frame[y][x]
    return colors



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