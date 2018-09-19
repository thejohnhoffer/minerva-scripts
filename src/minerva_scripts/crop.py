''' Test to crop all tiles in a region
'''
from minerva_lib import crop


def do_crop(load_tile, channels, tile_shape, full_origin, full_shape,
            levels=1, max_size=2000):
    ''' Interface with minerva_lib.crop

    Args:
        load_tile: Function to supply 2D numpy array
        channels: List of dicts of channel rendering settings
        tile_shape: The height, width of a single tile
        full_origin: Request's full-resolution y, x origin
        full_shape: Request's full-resolution height, width
        levels: The number of pyramid levels
        max_size: The maximum response height or width

    Returns:
        2D numpy float array of with height, width of at most max_size
        The array is a composite of all channels for full or partial
        tiles within `full_shape` from `full_origin`.
    '''

    level = crop.get_optimum_pyramid_level(full_shape, levels, max_size, False)
    crop_origin = crop.scale_by_pyramid_level(full_origin, level)
    crop_size = crop.scale_by_pyramid_level(full_shape, level)
    print(f'Cropping 1/{level} scale')

    image_tiles = []

    for channel in channels:

        (red, green, blue) = channel['color']
        _id = channel['channel']
        _min = channel['min']
        _max = channel['max']

        for indices in crop.select_tiles(tile_shape, crop_origin, crop_size):

            (y, x) = indices

            # Disallow negative tiles
            if y < 0 or x < 0:
                continue

            # Load image from Minerva
            image = load_tile(_id, level, y, x)

            # Disallow empty images
            if image is None:
                continue

            # Add to list of tiles
            image_tiles.append({
                'min': _min,
                'max': _max,
                'image': image,
                'indices': (y, x),
                'color': (red, green, blue),
            })

    return crop.composite_subtiles(image_tiles, tile_shape,
                                   crop_origin, crop_size)
