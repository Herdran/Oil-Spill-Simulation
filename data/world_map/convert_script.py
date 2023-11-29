import os

from PIL import Image
import numpy as np

DATA_PATH = 'data/world_map/original'
SAVE_PATH = 'data/world_map'


def get_save_file_name(original_path):
    return os.path.basename(original_path) + '.bin'


def convert_tif_to_binary(file_path):
    img = Image.open(file_path)
    img_array = np.array(img)
    binary_array = np.where(img_array < 0, 1, 0)
    binary_bytes = np.packbits(binary_array)

    with open(os.path.join(SAVE_PATH, get_save_file_name(file_path)), 'wb') as f:
       f.write(binary_bytes)


if __name__ == '__main__':
    Image.MAX_IMAGE_PIXELS = 999999999
    
    for file in os.listdir(DATA_PATH):
        if file.endswith('.tifx'):
            file = os.path.join(DATA_PATH, file)
            print(f'Converting {file}...')
            convert_tif_to_binary(file)
            print(f'Converted {file} -> {get_save_file_name(file)}')
            
