## ALUP Lightshow

A basic ALUP lightshow player. 
Play time stamp-based lightshows from json files to one or more ALUP LED Receivers.

**NEW:**
Generate simple light shows using `video`

## Setup
Note: Requires ALUP v.0.2.2+ (timesync + buffering)
- Install [pyalup](https://github.com/Skyfighter64/Python-ALUP/)
- Install [Arduino-ALUP](https://github.com/Skyfighter64/Arduino-ALUP) on the LED receivers

## Security Note:
Only use trusted light show json files, don't run files from untrused sources without verifying their contents.

## Running a light show:
1. Change the device connection parameters to your devices in your lightshow file (eg. for `example.json: Set the IP address for Device 0 and the COM-Port for device 1 correctly)
2. Run: `python3 lightshow/lightshow.py example.json`

## Create a lightshow from mp4:
1. In `video_to_lightshow.py`, set `NUM_LEDS` to the number of LEDS of your device
2. Set the video input and lightshow output paths in the same file.
3. run `python3 video_to_lightshow.py` to start conversion

**NOTE**: This script requires [opencv-python](https://pypi.org/project/opencv-python/)


## Manual Lightshow Configuration:
Define a json file with:
- a list of devices
- a list of frames with ascending timestamps in milliseconds 

Frame, Command and Device API are kept analogous to the [pyalup definitions](https://github.com/Skyfighter64/Python-ALUP/).

See 'example.json' for an example lightshow with two devices.

## Logging/debugging:
We use the python logging module. To specify the log level, change the level in `lightshow.py`