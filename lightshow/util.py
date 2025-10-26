"""
file containing a collection of utility and conversion functions
"""

import abc

class Convert():
    @abc.abstractmethod   
    def rgbToInt(rgb):
        color = 0
        color += rgb[2]
        color += (rgb[1] << 8)
        color += (rgb[0] << 16) 
        return color
    
    @abc.abstractmethod   
    def intToRGB(color):
        b =  color & 255
        g = (color >> 8) & 255
        r = (color >> 16) & 255
        return [r,g,b]
    
    def intColorToHex(color):
        return "0x{0:06x}".format(color)

    @abc.abstractmethod   
    def rgbToHex(r,g,b):
        return "0x{0:02x}{1:02x}{2:02x}".format(Convert.clamp(r), Convert.clamp(g), Convert.clamp(b))

    @abc.abstractmethod   
    def clamp(x): 
        return max(0, min(x, 255))
    





def test():
    # test rgb to int
    assert Convert.rgbToInt([255,255,255]) == 0xffffff
    assert Convert.rgbToInt([0,255,255]) == 0x00ffff
    assert Convert.rgbToInt([255,0,255]) == 0xff00ff
    assert Convert.rgbToInt([255,255,0]) == 0xffff00

    # test int to rgb
    assert Convert.intToRGB(0xffffff) == [255,255,255]
    assert Convert.intToRGB(0x00ffff) == [0,255,255]
    assert Convert.intToRGB(0xff00ff) == [255,0,255]
    assert Convert.intToRGB(0xffff00) == [255,255,0]

if __name__ == "__main__":
    test()