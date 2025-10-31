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
from pyalup.TcpConnection import TcpConnection
from pyalup.SerialConnection import SerialConnection


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

parser.add_argument('--serial', nargs=1, default=None, help="Specify a serial connected ALUP device replacing the first device of the lightshow: [PORT]{:[BAUD]} eg: COM7:115200. Default Baud:115200")
parser.add_argument('--tcp', nargs=1, default=None, help="Specify a TCP connected ALUP device replacing the first device of the lightshow. Format: [ip]{:[BAUD]} eg: 127.0.0.1:5012. Default Port: 5012")

def main():
    args = parser.parse_args()
    logging.basicConfig(format="[%(asctime)s %(levelname)s]: %(message)s", datefmt="%H:%M:%S")
    lightshow = Lightshow()
    SetLogLevel(lightshow.logger, args.loglevel)
    if(args.verbose):
        lightshow.logger.setLevel(logging.DEBUG)

    try:
        lightshow.fromJson(args.lightshow_file)
    except IndexError:
        logging.warning("No device specified in lightshow file. Please add a device to the JSON file.")

    # override device with commandline argument if given
    if(args.serial is not None):
        logging.info("Using Serial Device from Commandline Args: " + str(args.serial))
        if(len(lightshow.devices) == 0):
            lightshow.devices.append(Device())
            lightshow.frames.append([])
        lightshow.devices[0].connection = SerialConnectionFromString(args.serial[0])
    elif(args.tcp is not None):
        logging.info("Using TCP Device from Commandline Args: " + str(args.tcp))
        if(len(lightshow.devices) == 0):
            lightshow.devices.append(Device())
            lightshow.frames.append([])
        lightshow.devices[0].connection = TcpConnectionFromString(args.tcp[0])

    # establish connection
    lightshow.Connect()
    # calibrate time stamps
    lightshow.Calibrate()

    CountDown(args.countdown)

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


def CountDown(seconds):
    if (seconds > 0):
        print("----[ Starting in: ]----")
        for i in reversed(range(seconds + 1)):
            time.sleep(1)
            print(i)

# create an alup Serial connection from a string of connection parameters
# Format: [PORT]{:[Baud]}
# Default Baud: 115200
def SerialConnectionFromString(parameters : str):
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


if __name__=="__main__":
    main()