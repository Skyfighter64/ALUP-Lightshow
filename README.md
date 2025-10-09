## ALUP Lightshow

A basic ALUP lightshow player. 
Play time stamp-based lightshows from json files to one or more ALUP LED Receivers.

## Setup
Note: Requires ALUP v.0.2.2+ (timesync + buffering)
- Install [pyalup](https://github.com/Skyfighter64/Python-ALUP/)
- Install [Arduino-ALUP](https://github.com/Skyfighter64/Arduino-ALUP) on the LED receivers

## Configuration:
Define a json file with:
- a list of devices
- a list of frames with ascending timestamps in milliseconds 

Frame, Command and Device API are kept analogous to the [pyalup definitions](https://github.com/Skyfighter64/Python-ALUP/).

See 'example.json' for an example lightshow with two devices.

## Security Note:
Only use trusted light show json files, don't run files from untrused sources without verifying their contents.

## Usage:
1. Specify your json lightshow file in `lightshow.py: lightshow.fromJson()`
2. Run the lighthshow: `python3 lightshow.py`

## Logging/debugging:
We use the python logging module. To specify the log level, change the level in `lightshow.py`