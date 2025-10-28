import numpy as np
import cv2

import sys
import os
import time
import logging
import argparse
from pyalup.Frame import Frame 
from pyalup.Device import Device
from pyalup.TcpConnection import TcpConnection
from pyalup.SerialConnection import SerialConnection
from pathlib import Path
from enum import IntEnum

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from lightshow.lightshow import Lightshow
from lightshow.arrangement import Arrangement
from lightshow.postprocessing import Postprocessing
from lightshow.util import Convert

"""

Simple script turning a mp4 video file into a lightshow JSON which can be used with lightshow.py
Scales the given video down to one horizontal line of NUM_LED pixels. Only works for a single device.

"""
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def main():
    parser = argparse.ArgumentParser(prog="Video To Lightshow", description="Convert video files to ALUP light shows which can be played with the light show player", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # setup arg parser
    parser.add_argument('video_file', help="Specify a video file to create a lightshow from")
    parser.add_argument('-n', '--num_leds', default=10, type=int, help="Use a linear arrangement with n LEDs. Ignored if -a | --arrangement is used")   
    parser.add_argument('-o', '--output', default='output.json', help="The output json file to which the light show will be written.")
    parser.add_argument('-v', '--verbose', action='store_true', help="Enable verbose logging")  # on/off flag
    parser.add_argument('--suppress_live_view', action='store_true', help="Disable the live viewing window. Makes conversion a lot faster")
    parser.add_argument('--no_postprocessing', action='store_true', help="Disable postprocessing steps such as Contrast normailization")
    parser.add_argument('-a','--arrangement', default=None, help="Specify a bitmap file with the positions of the LEDs. The integer color value of each pixel represents the LEDs index. White (0xffffff) pixels are ignored")
    parser.add_argument('-i', '--interpolation', choices=[i.name for i in  InterpolationMode],default=InterpolationMode.area.name, help="Select an interpolation mode for conversion.")

    parser.add_argument('--serial', nargs=1, default=None, help="Specify a serial connected ALUP device to add to the light show file Format: [PORT]{:[BAUD]} eg: COM7:115200. Default Baud:115200")
    parser.add_argument('--tcp', nargs=1, default=None, help="Specify a TCP connected ALUP device to add to the light show file. Format: [ip]{:[BAUD]} eg: 127.0.0.1:5012. Default Port: 5012")

    # handle cmdline args
    args = parser.parse_args()

    device = Device()
    if(args.serial is not None):
        device.connection = SerialConnectionFromString(args.serial[0])
    elif(args.tcp is not None):
        device.connection = TcpConnectionFromString(args.tcp[0])
    else:
        # don't add device because it is not specified
        device = None

    if(args.verbose):
        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)

    # choose interpolation mode 
    interpolation = InterpolationMode[args.interpolation].value


    # read in LED arrangement
    logger.info("Generating arrangement from bitmap " + str(args.arrangement))
    arrangement = Arrangement()
    
    if(args.arrangement is not None):
        arrangement.FromBitmap(args.arrangement)
    else:
        arrangement.Linear(args.num_leds)
    mask = arrangement.GetMask()

    #logger.debug("Mask" + str(mask))  
    cap = cv2.VideoCapture(args.video_file)
    show = Lightshow()

    # add the device to the show
    if device is not None:
        show.devices.append(device)

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
        resized_frame = cv2.resize(frame, arrangement.shape, interpolation=interpolation)
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

    if (not args.no_postprocessing):
        logger.info("Doing post processing:")
        logger.info(" - Contrast normalization")
        for frames in show.frames:
         frames = Postprocessing.NormalizeContrast(frames)

    # show the final result for debug purposes
    if (logger.level <= logging.DEBUG):
        logger.info("Showing final result. Press q to on video to skip")
        for frame in show.frames[0]:
            cv2.imshow("Final result", cv2.resize(cv2.cvtColor(np.array([[Convert.intToRGB(color) for color in frame.colors]], dtype=np.uint8), cv2.COLOR_RGB2BGR), None, fx=25, fy = 25, interpolation = cv2.INTER_NEAREST))
            if cv2.waitKey(30) & 0xFF == ord('q'):
                break


    # close all cv2 related stuff
    cap.release()
    cv2.destroyAllWindows()

   


    logger.info("Converting to JSON")
    # export the lightshow as json
    show.toJson(args.output, comments=[f"Converted from '{Path(args.video_file).name}'", f"Arrangement: {arrangement.name}", f"Interpolation: {args.interpolation}"])
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

# create an alup Serial connection from a string of connection parameters
# Format: [PORT]{:[Baud]}
# Default Baud: 115200
def SerialConnectionFromString(parameters : str):
    print(parameters)
    splitted = parameters.split(':')
    port = splitted[0]
    baud = int(splitted[1]) if len(splitted) > 1 else 115200
    return SerialConnection(port, baud)

# create an alup tcp connection from a string of connection parameters
# Format: [ip]{:[port]}
# Default port: 5012
def TcpConnectionFromString(parameters : str):
    splitted = parameters.split(':')
    ip = splitted[0]
    port = int(splitted[1]) if len(splitted) > 1 else 5012
    return TcpConnection(ip, port)


# add a frame with the given colors and the given time stamp
# to the given lightshow
# @param lightshow: a lightshow object
# @param colors: an array of hexadecimal RGB values
# @param timestamps: the time stamp in ms of the given frame
def AddFrameToLightshow(lightshow, colors, timestamp):
    frame = Frame()
    frame.colors = [Convert.rgbToInt(color) for color in colors]
    frame.timestamp = timestamp

    # NOTE: currently, this will only work for one single device
    lightshow.frames[0].append(frame)



class InterpolationMode(IntEnum):
    linear = cv2.INTER_LINEAR
    area = cv2.INTER_AREA
    nearest = cv2.INTER_NEAREST
    cubic = cv2.INTER_CUBIC

    def __str__(self):
        return self.value
    
    

if __name__ == "__main__":
    main()