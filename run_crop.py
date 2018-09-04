''' Test to crop all tiles in a region
'''
import os
import sys
import pathlib
import argparse
import skimage.io
import numpy as np
from minerva_scripts.crop import do_crop
from minerva_scripts.aws_srp import AWSSRP
from minerva_scripts.omeroapi import OmeroApi
from minerva_scripts.minervaapi import MinervaApi


if __name__ == '__main__':

    args = sys.argv[1:]

    # Read from a configuration file at a default location
    cmd = argparse.ArgumentParser(
        description='Crop a region'
    )

    default_url = '/0/0/?c=1|0:65535$FF0000'
    default_url += '&region=0,0,1024,1024'
    cmd.add_argument(
        'url', nargs='?', default=default_url,
        help='OMERO.figure render_scaled_region url'
    )
    cmd.add_argument(
        '-o', default=str(pathlib.Path.cwd()),
        help='output directory'
    )

    parsed = cmd.parse_args(args)
    out_file = str(pathlib.Path(parsed.o, 'out.png'))

    # Set up AWS Authentication
    try:
        username = os.environ['MINERVA_USERNAME']
    except KeyError:
        print('must have MINERVA_USERNAME in environ', file=sys.stderr)
        sys.exit()

    try:
        password = os.environ['MINERVA_PASSWORD']
    except KeyError:
        print('must have MINERVA_PASSWORD in environ', file=sys.stderr)
        sys.exit()

    minerva_pool = 'us-east-1_YuTF9ST4J'
    minerva_client = '6ctsnjjglmtna2q5fgtrjug47k'
    uuid = '0af50f96-3b0f-467d-aa29-ecbe1935f1bf'
    minerva_bucket = 'minerva-test-cf-common-tilebucket-1su418jflefem'
    minerva_domain = 'lze4t3ladb.execute-api.us-east-1.amazonaws.com/dev'

    srp = AWSSRP(username, password, minerva_pool, minerva_client)
    result = srp.authenticate_user()
    token = result['AuthenticationResult']['IdToken']

    # Read parameters from URL and API
    split_url, query_dict = OmeroApi.read_url(uuid + parsed.url)
    keys = OmeroApi.scaled_region(split_url, query_dict, token,
                                  minerva_bucket, minerva_domain)

    # Make array of channel parameters
    inputs = zip(keys['chan'], keys['c'], keys['r'])
    channels = map(MinervaApi.format_input, inputs)

    # Minerva loads the tiles
    def ask_minerva(c, l, i, j):
        keywords = {
            't': 0,
            'z': 0,
            'l': l,
            'x': i,
            'y': j
        }
        limit = keys['limit']
        return MinervaApi.image(uuid, token, c, limit, **keywords)

    # Minerva does the cropping
    out = do_crop(ask_minerva, channels, keys['tile_size'],
                  keys['origin'], keys['shape'], keys['levels'],
                  keys['max_size'])

    # Write the image buffer to a file
    try:
        skimage.io.imsave(out_file, np.uint8(255 * out))
    except OSError as o_e:
        print(o_e)
