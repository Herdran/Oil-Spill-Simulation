import os
import bitarray

def get_binary_files() -> list:
    DATA_PATH = 'data/world_map/bin'
    files = []    
    for file in os.listdir(DATA_PATH):
        if file.endswith('.bin'):
             files.append(os.path.join(DATA_PATH, file))
    return files


def read_binaries(files: list[os.PathLike]) -> list:
    binaries = []
    for file in files:
        with open(file, 'rb') as f:
            array = bitarray.bitarray()
            array.fromfile(f)
            binaries.append(array)
    return binaries


if __name__ == "__main__":    
    SIDE_COUNT = 21600
    
    X_BIN_COUNT = 4
    Y_BIN_COUNT = 2
    
    binaries = read_binaries(get_binary_files())
   
    print("Merging binaries...")
    
    result_binary = bitarray.bitarray()
    for bin_row in range(Y_BIN_COUNT):
        for row in range(SIDE_COUNT):
            print(f"progress: {row/SIDE_COUNT}")
            for bin_col in range(X_BIN_COUNT):
                for col in range(SIDE_COUNT):
                    image_index = (bin_row * X_BIN_COUNT) + bin_col
                    bit_index = (row * SIDE_COUNT) + col
                    result_binary.append(binaries[image_index][bit_index])
                    
    RESULT_PATH = "data/world_map/full_world_map.bin"
    with open(RESULT_PATH, 'wb') as file:
        result_binary.tofile(file)
   
    print(f"Saved to: {RESULT_PATH}")
                
                            

    