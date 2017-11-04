#!python

import sys
import PIL.ImageDraw

if __name__ == '__main__':
    path = sys.argv[1]
    im = PIL.ImageDraw.Image.open(path)
    print(im.size)
