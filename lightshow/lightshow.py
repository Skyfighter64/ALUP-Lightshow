import json
import logging
import time
import threading
import uuid
import pyalup
from pyalup.Device import Device
from pyalup.Frame import Frame, Command
from tqdm import tqdm


class Lightshow:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # NOTE: Don't use pyalup.Group here because we are not necessarily running devices synchronized (???)
        self.devices = []
        self.frames = [] # 2d-array with frames for each device

        # start time of the lightshow in ms
        self.t_start = 0
        self._skip_late_frames = True

    
    
    def Run(self, speed=1):
        # initialize start time 
        self.t_start = time.time_ns() // 1000000
        self.logger.info(f"Start running lightshow at {speed}x speed")
        self.logger.info("at " + str(time.strftime('%d.%m.%y %Hh:%Mm:%Ss', time.gmtime(self.t_start / 1000))))


        self.logger.debug("Registering threads")
        # register threads for each device
        threads = []
        # configure one thread for each device
        for i, device in enumerate(self.devices):
            thread = threading.Thread(target=self._RunLightshow(device, self.frames[i], speed))
            threads.append(thread)

        self.logger.debug(f"Registered {len(self.devices)} thread(s)")

        # start all threads
        self.logger.debug("Starting threads")
        for thread in threads:
            thread.start()

        # wait for all threads to finish

        for thread in threads:
            thread.join()

        # wait for all outstanding answers

        for device in self.devices:
            self.logger.debug("Flushing buffer for device " + str(device.configuration.deviceName))
            device.FlushBuffer()

        self.logger.info("Done.")
        

    def _RunLightshow(self, device, frames, speed = 1):
        # calibrate time synchronization
        #self.logger.debug("Calibrating device")
        #device.Calibrate()
        self.logger.debug(f"Playing {len(frames)} frames")

        # enable progress bar for log level INFO and below
        if self.logger.level <= logging.INFO:
            _frames = tqdm(frames)
        else:
            _frames = frames 

        # track number of skipped frames 
        skipped_frames = 0

        for frame in _frames:
            # make timestamp relative to start point in time
            # NOTE: we used a hack previously to store the relative time in the time stamp
            relative_timestamp = frame.timestamp
            frame.timestamp = (frame.timestamp // speed) + self.t_start

            # ignore frame if already too late
            self.logger.debug(f"Frame time stamp: {frame.timestamp}, now: {time.time() * 1000}, device latency: {device.latency}, Skipping frame? {frame.timestamp <= (time.time()* 1000) + device.latency//2}")
            if(self._skip_late_frames and frame.timestamp <= (time.time() * 1000) + device.latency//2):
                # reset the time stamp to the relative time stamp
                # NOTE: this only works because ALUP makes a copy of the frame before sending
                frame.timestamp = relative_timestamp
                skipped_frames += 1
                self.logger.debug("Connection too slow; Skipping frame")
                continue

            device.frame = frame
            device.Send()
            
            self.logger.debug("Sent frame to device " + str(device.configuration.deviceName) + "\n"+ str(frame))
            # reset the time stamp to the relative time stamp
            # NOTE: this only works because ALUP makes a copy of the frame before sending
            frame.timestamp = relative_timestamp
        self.logger.info(f"Device {device.configuration.deviceName} skipped {skipped_frames} frames total ({skipped_frames / len(frames)}%)")

    # calibrate time synchronization for all devices
    def Calibrate(self):
        # calibrate devices
        self.logger.info("Calibrating devices")
        for device in self.devices:
            device.Calibrate()

        

    # convert the lightshow to a json file and save it to the given pat
    def toJson(self, output_path, comments = None):
        #print(json.dumps(self))
        data = {
            "devices" : self._DevicesToJSON,
            "timeline" : self._FramesToJson()
        }
        if (comments is not None):
            data['comments'] = comments

        data['devices'] = self._DevicesToJSON()
        data['timeline'] = self._FramesToJson()
        json_string = json.dumps(data, cls=NoIndentEncoder, indent=4)
        with open(output_path, "w+") as f:
            f.write(json_string)
        

    def _DevicesToJSON(self):
        # TODO not implemented yet
        return []

    # convert all frames of this lightshow to json format
    def _FramesToJson(self):
        out =  []
        for i in range(len(self.frames)):
            for frame in self.frames[i]:
                out.append(NoIndent({
                        "timestamp" : frame.timestamp,
                        "device" : i,
                        "offset" : frame.offset,
                        "command" : frame.command.name,
                        "colors" : [str(color) for color in frame.colors]
                        }))
        return out



    def __str__(self):
        return "Lightshow: \nDevices: " + str(self.devices) + "\nFrames: " +  str(self.frames) 

    def fromJson(self, filename):
        with open(filename) as f:
            # 1. load in json
            self.logger.info("Loading lightshow from file '" + str(filename) + "'")
            data = json.load(f)
            # 2. initialize ALUP devices from json file 
            self._devicesFromJson(data)
            self.logger.info("Connected to " + str(len(self.devices)) + " devices")
            # 3. Load all animation steps (one array for each device)
            self._framesFromJson(data)
            self.logger.info("Loaded Frames for each device: " + str([len(i) for i in self.frames]))


    # load and initialize devices from a json object
    # NOTE: Devices are added in the same order as they appear in the JSON file
    def _devicesFromJson(self, data):
        for device_data in data["devices"]:
            device = Device()
            self.logger.debug("Connecting to : " + str(device_data))
            if device_data["connection"] == "tcp":
                # TODO: it is probably NOT a good idea to blindly connect to any given ip, is it?
                # the animation file NEEDS to be trustworthy
                device.TcpConnect(ip=device_data["address"], port=int(device_data["port"]))
            elif device_data["connection"] == "serial":
                device.SerialConnect(port=device_data["port"], baud=int(device_data["baud"]))
            else:
                self.logger.error("Can't connect to device: Unknown connection type: " + str(device_data["connection"]))
                return
            # add device to lightshow
            self.devices.append(device)
            self.logger.debug("Connected to device: " + str(device.configuration))
            # add an array to store the device's frames
            self.frames.append([])


    def _framesFromJson(self, data):
        for frame_data in data["timeline"]:
            frame = Frame()
            # HACK: we store the relative timestamp in the field for the absolute timestamp
            # TODO: Remember to add the light show start time to the timestamp before applying  
            frame.timestamp = frame_data["timestamp"]
            frame.offset = frame_data["offset"]
            frame.command = Command[frame_data["command"]]
            # convert the array of hex strings to integer colors
            # TODO: maybe do integrity checking (if string is real 24bit color)
            frame.colors = [int(value, 16) for value in frame_data["colors"]]

            # add frame to frame list for the device
            self.frames[frame_data["device"]].append(frame)
            self.logger.debug("Loaded frame: " + str(frame))


"""
    Prettier JSON encoder
    Credits: https://stackoverflow.com/a/25935321
"""
class NoIndent(object):
    def __init__(self, value):
        self.value = value


class NoIndentEncoder(json.JSONEncoder):
    def __init__(self, *args, **kwargs):
        super(NoIndentEncoder, self).__init__(*args, **kwargs)
        self.kwargs = dict(kwargs)
        del self.kwargs['indent']
        self._replacement_map = {}

    def default(self, o):
        if isinstance(o, NoIndent):
            key = uuid.uuid4().hex
            self._replacement_map[key] = json.dumps(o.value, **self.kwargs)
            return "@@%s@@" % (key,)
        else:
            return super(NoIndentEncoder, self).default(o)

    def encode(self, o):
        result = super(NoIndentEncoder, self).encode(o)
        for k, v in iter(self._replacement_map.items()):
            result = result.replace('"@@%s@@"' % (k,), v)
        return result
    

