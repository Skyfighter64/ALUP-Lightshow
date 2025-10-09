import json
import logging
import time
import threading
import pyalup
from pyalup.Device import Device
from pyalup.Frame import Frame, Command



def main():
    logging.basicConfig(format="[%(asctime)s %(levelname)s]: %(message)s", datefmt="%H:%M:%S")
    lightshow = Lighshow()
    lightshow.logger.setLevel(logging.INFO)
    
    # load lightshow from json file
    lightshow.fromJson("example.json")
    # calibrate time stamps
    lightshow.Calibrate()
    # run light show
    lightshow.Run()

    # disconnect devices when we are done
    for device in lightshow.devices:
        if device.connected:
            device.Disconnect()



class Lighshow:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # NOTE: Don't use pyalup.Group here because we are not necessarily running devices synchronized (???)
        self.devices = []
        self.frames = [] # 2d-array with frames for each device

        # start time of the lightshow in ms
        self.t_start = 0
        pass
    
    
    def Run(self):
        # initialize start time 
        self.t_start = time.time_ns() // 1000000
        self.logger.info("Start running lightshow")
        self.logger.info("at " + str(time.strftime('%d.%m.%y %Hh:%Mm:%Ss', time.gmtime(self.t_start / 1000))))

        self.logger.debug("Registering threads")
        # register threads for each device
        threads = []
        # configure one thread for each device
        for i, device in enumerate(self.devices):
            thread = threading.Thread(target=self._RunLightshow(device, self.frames[i]))
            threads.append(thread)

        # start all threads
        self.logger.debug("Starting threads")
        for thread in threads:
            thread.start()

        # wait for all threads to finish

        for thread in threads:
            thread.join()

        # wait for all outstanding answers
        self.logger.debug("Flushing buffer for device " + str(device.configuration.deviceName))
        for device in self.devices:
            device.FlushBuffer()

        self.logger.info("Done.")
        

    def _RunLightshow(self, device, frames):
        # calibrate time synchronization
        device.Calibrate()
        for frame in frames:
            # make timestamp relative to start point in time
            # NOTE: we used a hack previously to store the relative time in the time stamp
            frame.timestamp = frame.timestamp + self.t_start
            device.frame = frame
            device.Send()
            self.logger.debug("Sent frame to device " + str(device.configuration.deviceName) + "\n"+ str(frame))
        # wait for all outstanding answers
        self.logger.debug("Flushing buffer for device " + str(device.configuration.deviceName))

    # calibrate time synchronization for all devices
    def Calibrate(self):
        # calibrate devices
        self.logger.info("Calibrating devices")
        for device in self.devices:
            device.Calibrate()

        

    def toJson(self):
        # 1. write device configs to json

        # 2. write all animation steps 
        pass

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

if __name__=="__main__":
    main()