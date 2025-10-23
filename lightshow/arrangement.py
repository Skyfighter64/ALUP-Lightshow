import logging
import cv2
import numpy as np

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


    def Linear(self, n: int, height = 0):
        """
        Initialize a simple linear LED arrangement as one line from left to right
        @param n: The number of LEDs in the arrangement
        @param offset: The offset from the first LED
        @param height: The y-position of the arrangement. Default 0
        """
        self.shape = (n, 1 + height)
        self.coordinates = [(i,i, height) for i in range(n,)]

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
