import json
import logging
import time
import os
import threading
import uuid
import sys
import argparse
import pyalup
from pyalup.Device import Device
from pyalup.Frame import Frame, Command


SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from lightshow.lightshow import Lightshow

parser = argparse.ArgumentParser(prog="Lightshow Player", description="Play back lightshow JSON files")
# setup arg parser
parser.add_argument('lightshow_file', help="Specify a JSON file containing a light show")
parser.add_argument('-c', '--countdown', default=0, type=int, help="Show a countdown in seconds before the light show starts") 
parser.add_argument('--loop', action='store_true', help="Loop the light show indefinitely") 
parser.add_argument('-v', '--verbose', action='store_true', help="Enable verbose logging") 
parser.add_argument('--speed', default=1, type=float, help="The playback speed multiplier. Default 1") 
parser.add_argument('--loglevel', default='INFO', help='Specify the minimum level for log messages (Either String or Int value). Possible log levels: NOTSET (0), DEBUG (10), INFO (20), WARNING (30), ERROR (40), CRITICAL (50). Default: INFO')

def main():
    args = parser.parse_args()


    logging.basicConfig(format="[%(asctime)s %(levelname)s]: %(message)s", datefmt="%H:%M:%S")

    lightshow = Lightshow()
    SetLogLevel(lightshow.logger, args.loglevel)

    if(args.verbose):
        lightshow.logger.setLevel(logging.DEBUG)
    
     # load lightshow from json file
    try:
        lightshow.fromJson(args.lightshow_file)
    except IndexError:
        logging.error("No device specified in lightshow file. Please add a device to the JSON file.")
        exit()

    # calibrate time stamps
    lightshow.Calibrate()

    # countdown
    if (args.countdown > 0):
        print("----[ Starting in: ]----")
        for i in reversed(range(args.countdown + 1)):
            time.sleep(1)
            print(i)

    try:
        # run light show
        while True:
            lightshow.Run(args.speed)
            if(not args.loop):
               break
    except KeyboardInterrupt:
        print("CTL + C pressed, stopping.")

    # disconnect devices when we are done
    for device in lightshow.devices:
        if device.connected:
            device.Clear()
            device.Disconnect()


def SetLogLevel(logger, level):
    """Get or set the log level.
    Usage: loglevel [level]
    @param level: the log level to set (int or string).
    Possible log levels:
        NOTSET (0)
        DEBUG (10)
        INFO (20)
        WARNING (30)
        ERROR (40)
        CRITICAL (50)
    """
    # set the new log level
    try:
        logger.setLevel(level)
    except ValueError:
        print("Unknown Log Level: " + str(level))

if __name__=="__main__":
    main()