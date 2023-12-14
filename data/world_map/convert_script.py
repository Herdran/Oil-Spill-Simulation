import os

from PIL import Image
import numpy as np

DATA_PATH = 'data/world_map/original'
SCALE_PATH = 'data/world_map/scaled'
SAVE_PATH = 'data/world_map'

SCALE_FACTOR = 6 


def get_save_file_name(original_path):
    return os.path.basename(original_path) + '.bin'


def convert_tif_to_binary(file_path):
    img = Image.open(file_path)
    img_array = np.array(img)
    binary_array = np.where(img_array < 0, 1, 0)
    binary_bytes = np.packbits(binary_array)

    with open(os.path.join(SAVE_PATH, get_save_file_name(file_path)), 'wb') as f:
       f.write(binary_bytes)


def get_tif_file_path():
    return DATA_PATH if SCALE_FACTOR == 1 else SCALE_PATH

if __name__ == '__main__':
    Image.MAX_IMAGE_PIXELS = 999999999
    
    for file in os.listdir(DATA_PATH):
        print(f'Processing {file}...')
        if not file.endswith('.tif'): 
            continue
        if SCALE_FACTOR > 1:
            print(f'Scaling {file} by {SCALE_FACTOR}...')
            img = Image.open(os.path.join(DATA_PATH, file))
            img = img.resize((img.width // SCALE_FACTOR, img.height // SCALE_FACTOR), Image.ANTIALIAS)
            img.save(os.path.join(SCALE_PATH, file))
            print(f'Scaled {file} by {SCALE_FACTOR} -> size {img.width}x{img.height}')
        file_path = os.path.join(get_tif_file_path(), file)
        print(f'Converting {file}...')
        convert_tif_to_binary(file_path)
        print(f'Converted {file} -> {get_save_file_name(file)}')
            
