#!/usr/bin/env python
"""
Uncrop an image. Undoes ExtractRegionFromImageByMask.
"""


import sys
import os
import re


def uncrop_by_mask(input_image, output_image, full_mask, padding=0, canvas=None, log_file=None):
    """
    Uncrop an image. Undoes ExtractRegionFromImageByMask.
    - log_file can be output from ExtractRegionFromImageByMask, otherwise it should be a mask image
    and the output will be generated by re-running ExtractRegionFromImageByMask.  padding is only relevant in the latter case.
    - canvas can be an image to paste the input into, otherwise it's blank 0s.
    """
    if log_file is None:
        # Need to discover the bounding box
        cmd = r"ExtractRegionFromImageByMask 3 %s %s %s 1 %s" % (full_mask, output_image, full_mask, padding)
        s = os.popen(cmd).read()
    else:
        # The log file of ExtractRegionFromImageByMask is given
        with open(log_file, 'r') as f:
            s = f.read()
    s = s.split('final cropped region')[-1]
    crop_index = re.search('Index:\s+\[(.*?)\]', s).group(1).replace(', ', 'x')
    if canvas is None:
        canvas = output_image
        cmd = 'CreateImage 3 %s %s 0' % (full_mask, canvas)
        os.system(cmd)
    cmd = 'PasteImageIntoImage 3 %s %s %s %s -1 1' % (canvas, input_image, output_image, crop_index)
    os.system(cmd)

if __name__ == '__main__':
    if len(sys.argv[1:]) < 3:
        print ('%s input_image output_image full_mask <padding> <canvas_image>' % sys.argv[0])
        sys.exit(0)
    input_image = sys.argv[1]
    output_image = sys.argv[2]
    full_mask = sys.argv[3]
    try:
        padding = sys.argv[4]
    except IndexError:
        padding = 0
    try:
        canvas = sys.argv[5]
    except IndexError:
        canvas = None

    uncrop_by_mask(input_image, output_image, full_mask, padding, canvas)
