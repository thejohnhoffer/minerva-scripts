''' Test to combine all channels for all tiles
'''
from ..load import disk
from ..write import precompute
from ..helper import config
import numpy as np
import argparse
import pathlib
import json
import cv2
import sys
import os


def lod_index_shape(zyx_shape, lod):
    ''' calculate index of last tile in lod

    Arguments:
        zyx_shape: zyx indices at full resolution
        lod: any power-of-2 resolution

    Returns:
        zyx indices at lod
    '''
    zyx_res = (1, 2 ** lod, 2 ** lod)
    return (zyx_shape - 1) // zyx_res


def lod_voxel_shape(last_tile, block_shape, lod_zyx):
    ''' calculate full shape at given level of detail

    Arguments:
        last_tile: the last tile for lod
        block_shape: the z,y,x shape of normal tiles
        lod_zyx: the index of last tile in lod

    Returns:
        np.uint32 Z,Y,X array of voxel shape for LOD
    '''
    margin = np.uint32((1,) + last_tile.shape)
    return margin + block_shape * lod_zyx


def main(args=sys.argv[1:]):
    ''' Convert all tiles to precompute directory structure
    for neuroglacner
    '''
    # Read from a configuration file at a default location
    cmd = argparse.ArgumentParser(
        description='combine channels for all tiles'
    )
    cmd.add_argument(
        '-o', default=str(pathlib.Path.cwd()),
        help='output directory'
    )
    cmd.add_argument(
        '-i', required='True',
        help='input directory'
    )

    parsed = vars(cmd.parse_args(args))
    # Actually parse and read arguments
    terms = config.parse(**parsed)

    # Full path format of input files
    in_path_format = terms['i']
    out_root = parsed['o']
    k_time = 0

    # Find range of image tiles
    ctlzyx_shape, tile_shape = disk.index(in_path_format)
    block_shape = np.uint32((1,) + tuple(tile_shape))

    # Parse key information about source
    zyx_shape = ctlzyx_shape[-3::]
    n_chan = ctlzyx_shape[0]
    n_lod = ctlzyx_shape[2]

    lod_list = []
    for lod in range(n_lod):

        # Data type at current LOD
        lod_zyx = lod_index_shape(zyx_shape, lod)
        tile_args = tuple(lod_zyx) + ([0], in_path_format)
        last_tile = disk.tile(0, lod, *tile_args)[0]
        dtype = str(last_tile.dtype)
        
        # Calculate voxel shape at LOD
        lod_voxels = lod_voxel_shape(last_tile, block_shape, lod_zyx)
        lod_list.append(lod_voxels)
    
    info = precompute.get_index(dtype, lod_list, block_shape)

    # Write metadata files
    for c in range(n_chan):

        # Make output per channel
        c_root = os.path.join(out_root, str(c))
        if not os.path.exists(c_root):
            os.makedirs(c_root)

        # Write metadata to channel directory
        c_info_path = os.path.join(c_root, 'info')
        with open(c_info_path, 'w') as info_file:
            json.dump(info, info_file)

        # Make directory for all levels of detail:
        for lod in range(n_lod):

            lod_root = os.path.join(c_root, str(lod))
            if not os.path.exists(lod_root):
                os.makedirs(lod_root)

            # Process all z, y, x tiles
            for i in range(np.prod(zyx_shape)):
                z, y, x = np.unravel_index(i, zyx_shape)

                # from disk, load all channels for tile
                all_buffer = disk.tile(k_time, lod, z, y, x,
                                       [c], in_path_format)

                # Continue if no channel buffers for given tile
                image = next((b for b in all_buffer), None)
                if image is None:
                    continue

                # write output jpeg
                out_path = precompute.get_path(image, [z, y, x],
                                               block_shape, lod)
                full_out_path = os.path.join(c_root, out_path)
                jpeg_out_path = full_out_path + '.jpg'

                # Write jpeg without extension
                if os.path.exists(full_out_path):
                    os.remove(full_out_path)

                cv2.imwrite(jpeg_out_path, image)

                try:
                    os.rename(jpeg_out_path, full_out_path)
                except OSError as o_e:
                    print(o_e)


if __name__ == '__main__':
    main(sys.argv)