import abc
import colorsys

from pyalup.Frame import Frame

from .util import Convert 

class Postprocessing:
    """
    Class with a collection of functions for filtering one or a list of ALUP frames
    """
    @abc.abstractmethod    
    def NormalizeContrast(frames, min_brightness = 0, max_brightness = 1.0):
        """
        Normalize the contrast / brightness of a list of Frames to fill the full 0-255 dynamic range
        @param frames: an array of frames each containing an array of Integer color values
        @param min_brightness: the minimum floatingpoint brightness of the result (0.0 - 1.0). Default: 0
        @param max_brightness: the maximum  floatingpoint brightness of the result (0.0 - 1.0). Default: 1.0

        @returns: the normalized frames
        """

        darkest_pixel = 1.0
        brightest_pixel = 0.0



        # find the brightest and darkest pixel
        for frame in frames:
            for j in range(len(frame.colors)):
                # convert to HSV
                pixel = Convert.intToRGB(frame.colors[j])
                pixel = colorsys.rgb_to_hsv(pixel[0] / 255, pixel[1] / 255, pixel[2] / 255)

                # save the brightest and darkest pixel value of all frames
                if pixel[2] < darkest_pixel:
                    darkest_pixel = pixel[2]
                if pixel[2] > brightest_pixel :
                    brightest_pixel = pixel[2]

        #print(f"Old min: {darkest_pixel}, old max {brightest_pixel}")

        # normalize each colors contrast
        for frame in frames:
            for j in range(len(frame.colors)):
                # get the current pixel value
                pixel = Convert.intToRGB(frame.colors[j])
                #print(f"input pixel {pixel}")
                pixel = colorsys.rgb_to_hsv(pixel[0] / 255, pixel[1] / 255, pixel[2] / 255)
                #print(f"hsv input pixel {pixel}")
                # normalize the pixel brightness to the new range
                new_value = (pixel[2] - darkest_pixel) * ((max_brightness-min_brightness)/(brightest_pixel-darkest_pixel)) + min_brightness
                #print(f"new value {new_value}")
                # convert back to RGB integer
                pixel = colorsys.hsv_to_rgb(pixel[0],pixel[1], new_value)
                pixel = [int(i * 255) for i in pixel ]
        
                # replace old pixel
                frame.colors[j] = Convert.rgbToInt(pixel)

        return frames
    

    def HighPass(frames, cuttoff):
        """
        Apply a high pass to the brightness of the given frames
        @param frames: an array of frames each containing an array of Integer color values
        @param cutoff: the minimum brightness value which will be part of the result (0-255)
        
        @returns: the frames with the high pass filter applied
        """
        for frame in frames:
            for j in range(len(frame.colors)):
                # convert to HSV
                pixel = Convert.intToRGB(frame.colors[j])
                pixel = colorsys.rgb_to_hsv(pixel[0] / 255, pixel[1] / 255, pixel[2] / 255)

                # save the brightest and darkest pixel value of all frames
                if pixel[2] * 255 < cuttoff:
                    # set the pixel to black
                    frame.colors[j] = 0x000000

        return frames


def test():
    # test high pass
    frame = Frame()
    frame.colors = [0x000000, 0x000a00, 0x000030, 0x020000, 0xffffff]
    result = Postprocessing.HighPass([frame], 128)
    assert result[0].colors == [0x000000, 0x000000, 0x000000, 0x000000, 0xffffff]

    # test normalization
    frame = Frame()
    frame.colors = [0x000000, 0x00ff00, 0x0000ff, 0xff0000, 0xffffff]
    result =  Postprocessing.NormalizeContrast([frame])[0]
    assert result.colors == [0x000000, 0x00ff00, 0x0000ff, 0xff0000, 0xffffff]

    frame.colors = [0x000000, 0x004400, 0x000044, 0x440000, 0x444444]
    result =  Postprocessing.NormalizeContrast([frame])[0]
    assert result.colors ==[0x000000, 0x00ff00, 0x0000ff, 0xff0000, 0xffffff]


if __name__ == "__main__":
    test()