import os

from PIL import Image
import numpy as np

def get_save_file_name(original_path):
    return os.path.basename(original_path) + '.bin'

def convert_tif_to_binary(file_path, threshold):
    img = Image.open(file_path)
    img_gray = img.convert('L')
    img_array = np.array(img_gray)
    binary_array = np.where(img_array <= threshold, 1, 0)
    binary_bytes = np.packbits(binary_array)

    with open(get_save_file_name(file_path), 'wb') as f:
        f.write(binary_bytes)


if __name__ == '__main__':
    Image.MAX_IMAGE_PIXELS = 999999999
    
    MAX_GRAY_VALUE = 255
    TRESHOLD = MAX_GRAY_VALUE / 2
    
    DATA_PATH = 'data/world_map/original'
    
    for file in os.listdir(DATA_PATH):
        if file.endswith('.tif'):
            file = os.path.join(DATA_PATH, file)
            print(f'Converting {file}...')
            convert_tif_to_binary(file, TRESHOLD)
            print(f'Converted {file} -> {get_save_file_name(file)}')