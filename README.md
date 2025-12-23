## ALUP Lightshow

A basic ALUP lightshow player. 
Play time stamp-based lightshows from json files to one or more ALUP LED Receivers.

**NEW:**
Generate simple light shows using `video_to_lightshow.py`

## Setup
Note: Requires ALUP v.0.3
- Install [pyalup](https://github.com/Skyfighter64/Python-ALUP/)
- Install [Arduino-ALUP](https://github.com/Skyfighter64/Arduino-ALUP) on the LED receivers

## Security Note:
Only use trusted light show json files, don't run files from untrused sources without verifying their contents.

## Running a light show:
1. Change the device connection parameters to your devices in your lightshow file (eg. for `example.json: Set the IP address for Device 0 and the COM-Port for device 1 correctly or specify device in cmdline options)
2. Run: `python3 lightshow_player.py [filename.json]`

There are some example light shows in `shows/examples` for:

- 100 LEDs in linear arrangement
- 10x LED Matrix arrangement
- custom 'zigzag' arrangement

You might need to change the device port/baud rate/... to fit your led setup.

The example arrangement files can be found in `arrangements/`

**NOTE**: Even though they are made for different arrangements, the lightshows can be run on any LED strip (disregarding arrangement/number of LEDs), but they won't look as intended.

## Create a lightshow from a Video:
Run `python3 video_to_lightshow.py [video_file.mp4] -o [output.json]` to start conversion
**NOTE:** `python3 video_to_lightshow.py --help` to find out more about the arguments

**NOTE**: This script requires [opencv-python](https://pypi.org/project/opencv-python/)
### Custom LED arrangements
When generating lightshows from videos, custom LED arrangements are supported by using Bitmaps.\
To do so, create a bitmap in the desired size and set the colors of individual pixels to the array indices. For example, place the color 0x000003 (R:0,G:0,B:3) anywhere on the Bitmap to set the position of the fourth pixel (with index 3) to this position. 

**NOTE**: When generating the light show, each video frame will be rescaled and interpolated to the size of the arrangement Bitmap. Therefore, pixels on small bitmaps cover more effective area than pixels on large bitmaps but are effected less by small changes in the video.

I found it best to use GIMP to create the arrangement Bitmaps, even though it is still tedious.

### Example arrangement bitmap for a linear 100-LED pattern:
<img src="./arrangements/linear.bmp" alt="Linear arrangement" width=100%  style="image-rendering: pixelated; image-rendering: crisp-edges;">

Github might have issues displaying these images correctly. See `./arrangements/linear.bmp` for unblurry version.

**NOTE**: Linear arrangements can also be produced programmatically without the use of bitmaps. See `lightshow/arrangement.py > class Arrangement > Linear()`

### Example arrangement bitmap for a custom zig-zag pattern:
<img src="./arrangements/zigzag.bmp" alt="Zig-zag arrangement" width=400  style="image-rendering: pixelated; image-rendering: crisp-edges;">

Github might have issues displaying these images correctly. See `./arrangements/zigzag.bmp` for unblurry version.

## Generate Lightshows from programs:
To create a lightshow from a custom python program, import `lightshow/lightshow.py` into your script and create a lightshow object.
Write your custom ALUP frames and ALUP devices into the respective arrays and call `lightshow.toJson()` to convert it into a JSON file.



## Manual Lightshow Configuration:
Light shows can also be written manually by hand. To do so:
Define a json file with:
- a list of devices
- a list of frames with ascending timestamps in milliseconds 

Frame, Command and Device API are kept analogous to the [pyalup definitions](https://github.com/Skyfighter64/Python-ALUP/).

### Example:
```json
{
    "devices" : [
        {"connection" : "tcp", "address" : "127.0.0.1", "port" : "5012"},
        {"connection" : "serial", "port" : "COM6", "baud" : "115200"}
    ],
    "timeline" : [
        {"timestamp" : 0, "device" : 0, "offset" : 0, "command" : "NONE", "colors" : ["0x000000", "0x000000", "0x000000", "0x000000"]},
        {"timestamp" : 0, "device" : 1, "offset" : 0, "command" : "NONE", "colors" : ["0x000000", "0x000000", "0x000000", "0x000000"]},
        {"timestamp" : 1000, "device" : 0, "offset" : 0, "command" : "NONE", "colors" : ["0xff0000", "0xff0000", "0xff0000", "0xff0000"]},
        {"timestamp" : 1500, "device" : 0, "offset" : 0, "command" : "NONE", "colors" : ["0x00ff00", "0x00ff00", "0x00ff00", "0x00ff00"]},
        {"timestamp" : 2000, "device" : 0, "offset" : 0, "command" : "NONE", "colors" : ["0x0000ff", "0x0000ff", "0x0000ff", "0x0000ff"]},
        {"timestamp" : 1000, "device" : 1, "offset" : 0, "command" : "NONE", "colors" : ["0xff0000", "0xff0000", "0xff0000", "0xff0000"]},
        {"timestamp" : 1500, "device" : 1, "offset" : 0, "command" : "NONE", "colors" : ["0x00ff00", "0x00ff00", "0x00ff00", "0x00ff00"]},
        {"timestamp" : 2000, "device" : 1, "offset" : 0, "command" : "NONE", "colors" : ["0x0000ff", "0x0000ff", "0x0000ff", "0x0000ff"]},
        {"timestamp" : 3000, "device" : 1, "offset" : 0, "command" : "CLEAR", "colors" : []},
        {"timestamp" : 4000, "device" : 1, "offset" : 0, "command" : "NONE", "colors" : ["0xff0000"]},
        {"timestamp" : 5000, "device" : 1, "offset" : 0, "command" : "NONE", "colors" : ["0x00ff00"]},
        {"timestamp" : 6000, "device" : 1, "offset" : 0, "command" : "NONE", "colors" : ["0x0000ff"]},
        {"timestamp" : 7000, "device" : 1, "offset" : 1, "command" : "NONE", "colors" : ["0xff0000"]},
        {"timestamp" : 8000, "device" : 1, "offset" : 1, "command" : "NONE", "colors" : ["0x00ff00"]},
        {"timestamp" : 9000, "device" : 1, "offset" : 1, "command" : "NONE", "colors" : ["0x0000ff"]},
        {"timestamp" : 10000, "device" : 1, "offset" : 2, "command" : "NONE", "colors" : ["0xff0000"]},
        {"timestamp" : 11000, "device" : 1, "offset" : 2, "command" : "NONE", "colors" : ["0x00ff00"]},
        {"timestamp" : 12000, "device" : 1, "offset" : 2, "command" : "NONE", "colors" : ["0x0000ff"]},
        {"timestamp" : 13000, "device" : 1, "offset" : 3, "command" : "NONE", "colors" : ["0xff0000"]},
        {"timestamp" : 14000, "device" : 1, "offset" : 3, "command" : "NONE", "colors" : ["0x00ff00"]},
        {"timestamp" : 15000, "device" : 1, "offset" : 3, "command" : "NONE", "colors" : ["0x0000ff"]},
        {"timestamp" : 16000, "device" : 0, "offset" : 0, "command" : "CLEAR", "colors" : []},
        {"timestamp" : 16000, "device" : 1, "offset" : 0, "command" : "CLEAR", "colors" : []}
    ]
}
```
See 'example.json' for an example lightshow with two devices.

## Logging/debugging:
We use the python logging module. To specify the log level, change the level in `lightshow.py` or use the command line arguments if available