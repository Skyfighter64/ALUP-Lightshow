import numpy as np
import cv2
from mss import mss
from PIL import Image
from pyalup.Device import Device 
import logging

sct = mss()
logging.basicConfig()

def main():
    arrangement = Arrangement()
    arrangement.FromBitmap("./arrangements/zigzag.bmp")

    device = Device()
    device.SerialConnect(port="COM6", baud=115200)


    ambilight = Ambilight(device, arrangement)

    try:
        ambilight.Run()
    except KeyboardInterrupt:
        device.Clear()
        device.Disconnect()
        cv2.destroyAllWindows()
        print("CTL+C pressed")


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
        while True:
            # screen grab the main monitor
            sct_img = sct.grab(sct.monitors[self.monitor])
            cv2.imshow('screen', cv2.resize(np.array(sct_img), None, fx=0.5, fy=0.5))

            # get colors from frame according to arrangement
            colors = self._SampleFromFrame(np.array(sct_img), self.arrangement)
            # send to ALUP Receiver
            self.device.SetColors(colors)
            self.device.Send()

            if (cv2.waitKey(1) & 0xFF) == ord('q'):
                cv2.destroyAllWindows()
                break

    # sample from a frame using the given arrangement tuples (index, x, y)
    def _SampleFromFrame(self, frame, arrangement):
        # resize to arrangement shape
        frame = cv2.resize(frame,arrangement.shape)
        # convert bgr to RGB
        # HACK: something is wrong when not converting TODO: fix this 
        rgb_frame =  cv2.cvtColor(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), cv2.COLOR_RGB2BGR)

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

# class for LED arrangements
class Arrangement():
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
    
    
def _RGBToInt(rgb):
    color = 0
    for c in rgb[::-1]:
        color = (color<<8) + c
    return int(color)



if __name__ == "__main__":
    main()