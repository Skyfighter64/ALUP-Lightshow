import numpy as np
import cv2
from mss import mss
from PIL import Image
from pyalup.Device import Device 
import logging

import cProfile


sct = mss()
logging.basicConfig()

def main():
    arrangement = Arrangement()
    #arrangement.FromBitmap("./arrangements/zigzag.bmp")
    arrangement.Linear(30)

    device = Device()
    #device.SerialConnect(port="COM6", baud=115200)
    device.SerialConnect(port="COM6", baud=250000)

    ambilight = Ambilight(device, arrangement)
    ambilight.logger.setLevel(logging.INFO)

    profiler = cProfile.Profile()
    profiler.runcall(ambilight.Run)

    profiler.print_stats(sort='cumtime')
        
    


class Ambilight():
    def __init__(self, device, arrangement, monitor = 0):
        """
        Default constructor
        @param device: List of ALUP devices to which the screen should be outputted
        @param arrangements: List of arrangements, one for each device
        @param monitor: the Index of the Monitor to grab. Default: 0
        
        """
        self.logger = logging.getLogger(__name__)
        self.monitor = monitor
        self.arrangement = arrangement
        self.device = device


    def Run(self):
        try:
            while True:
                # screen grab the main monitor
                sct_img = np.array(sct.grab(sct.monitors[self.monitor]))


                # convert color from CV2 convention to RGB
                rgb_frame = cv2.cvtColor(sct_img, cv2.COLOR_RGBA2RGB)

                # get colors from frame according to arrangement
                colors = self._SampleFromFrame(rgb_frame, self.arrangement)

                if (self.logger.level <= logging.INFO):
                    # show the extracted LED colors separately
                    # convert color from CV2 convention to RGB
                    #frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)
                    masked_frame = self.arrangement.MaskFrame(rgb_frame)
                    cv2.imshow('screen', cv2.resize(sct_img, None, fx=0.5, fy=0.5))
                    cv2.imshow("colors", cv2.resize(masked_frame, None, fx=25, fy = 25, interpolation = cv2.INTER_NEAREST))
                
                # send to ALUP Receiver
                self.device.SetColors(colors)
                self.device.Send()

                if (cv2.waitKey(1) & 0xFF) == ord('q'):
                    cv2.destroyAllWindows()
                    break
        except KeyboardInterrupt:
            self.device.Clear()
            self.device.Disconnect()
            cv2.destroyAllWindows()
            print("CTL+C pressed")

    # sample from a frame using the given arrangement tuples (index, x, y)
    def _SampleFromFrame(self, frame, arrangement):
        # resize to arrangement shape
        rgb_frame = cv2.resize(frame,arrangement.shape, interpolation=cv2.INTER_LINEAR)
        # extract color values
        colors = [0 for _ in range(len(arrangement.coordinates))]

        for led in arrangement.coordinates:
            index = led[0]
            x = led[1]
            y = led[2]
            # convert to hex color for ALUP
            colors[index] = _RGBToInt(rgb_frame[y][x])
        return colors

    def _RgbToHex(self, rgb):
        return "0x{0:02x}{1:02x}{2:02x}".format(self._clamp(rgb[0]), self._clamp(rgb[1]), self._clamp(rgb[2]))
    def _clamp(self, x): 
        return max(0, min(x, 255))



class Arrangement():
    """
    Class defining a 2-dimensional arrangement of LEDs
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.shape = None # 2D shape of the arrangement (width, height)
        self.coordinates = [] # array of coordinates and led Indices: (index, x, y), not necessarily sorted

    def FromBitmap(self, bitmap):
        """
        Initialize the arrangement from a bitmap file where the color of a pixel describes the index of a LED.
        Eg. The position of the pixel with color 0x000003 (0,0,3) will be the position of the LED with Index 3. 
        White Pixels will be ignored
        @param bitmap: the bitmap to load the arrangement from
        """
        self.logger.info("Loading arrangement from bitmap " + str(bitmap))
        image = cv2.imread(bitmap)

        if image is None:
            self.logger.error("Could not read Arrangement from file " + str(bitmap))
            return

        self.coordinates = []

        # convert the shape to (width, height)
        self.shape = (image.shape[1], image.shape[0])

        # extract the coordinates for each led from the image
        for y in range(self.shape[1]):
            for x in range(self.shape[0]):
                # convert the color of the pixel to an RGB index
                index = _RGBToInt(image[y][x])

                # check for duplicates
                if self._FindIndex(index) is not None:
                    self.logger.warning("Value " + str(index) + " found multiple times in bitmap, Ignoring...")
                    continue

                # ignore white pixels
                if (index == 0xffffff):
                    continue

                self.coordinates.append((index, x, y))


    def Linear(self, n: int):
        """
        Initialize a simple linear LED arrangement as one line from left to right
        @param n: The number of LEDs in the arrangement
        @param offset: The offset from the first LED
        """
        self.shape = (n, 1)
        self.coordinates = [(i,i,0) for i in range(n,)]

    def _FindIndex(self, index):
        """
        Finds the first coordinate with the given index in coordinates and returns it.
        Returns None if not existing
        """

        for coord in self.coordinates:
            if coord[0] == index:
                return coord
        return None

    def GetMask(self):
        """
        Return a RGB bit-mask describing according to the LED arrangement.
        Pixels which are part of the arrangement have value (255,255,255), others (0,0,0)
        """
        mask = np.zeros((self.shape[1], self.shape[0], 3), dtype=np.uint8)
        for led in self.coordinates:
            x = led[1]
            y = led[2]
            mask[y][x] = [255, 255, 255]
        return mask
    
    def MaskFrame(self, frame):
        """
        Applies a mask according to the arrangement to the given frame
        @param frame: A cv2 Mat or Numpy array containing image data
        @returns: the rescaled frame with only the LEDs set to color
        """
        # rescale frame to arrangement resolution
        resized_frame = cv2.resize(frame, self.shape)
        # apply mask
        masked_frame = cv2.bitwise_and(resized_frame, self.GetMask())

        return masked_frame
    
    
def _RGBToInt(rgb):
    color = 0
    for c in rgb[::-1]:
        color = (color<<8) + c
    return int(color)



if __name__ == "__main__":
    main()