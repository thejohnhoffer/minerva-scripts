from io import BytesIO
import numpy as np
import cv2
import boto3
from minerva_lib.blend import composite_channel
import time
import sys


def _s3_get(bucket, key):
    '''Fetch a specific PNG from S3 and decode'''

    obj = boto3.resource('s3').Object(bucket, key)
    stream = BytesIO()
    obj.download_fileobj(stream)

    image = cv2.imdecode(np.fromstring(stream.getvalue(), dtype=np.uint8), 0)

    return image


def _hex_to_rgb(color):
    '''Convert hex color to RGB'''

    # Check for the right format of hex value
    if len(color) != 6:
        raise ValueError('Hex color value {} invalid'.format(color))

    # Convert to BGR
    try:
        return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        raise ValueError('Hex color value {} invalid'.format(color))


def main(args=sys.argv[1:]):

    bucket = 'minerva-test-images'
    tiles = ['png_tiles/C0-T0-Z0-L0-Y0-X0.png']

    start = time.time()

    images = [_s3_get(bucket, tile) for tile in tiles]

    channels = [{
        'index': 0,
        'color': np.float32([c / 255 for c in _hex_to_rgb('ff0000')]),
        'min': 0,
        'max': 0.1
    }]

    read_in = time.time()

    shape = images[0].shape
    shape_color = shape + (3,)
    out = np.zeros(shape_color, dtype=np.float32)

    for channel, image in zip(channels, images):

        composite_channel(out, image, channel['color'],
                          channel['min'], channel['max'], out)

        cv2.imwrite('image{}.png'.format(channel['index']), image)

    blended = time.time()

    # retval, image = cv2.imencode('.png', out)
    cv2.imwrite('test.png', out)

    encoded = time.time()

    print('read_in', read_in - start)
    print('blended', blended - read_in)
    print('encoded', encoded - read_in)
