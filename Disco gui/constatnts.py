POINT_SIDE_SIZE = 50  # [m]
CELL_SIDE_SIZE = 10
GRID_SIDE_SIZE = 10
WORLD_SIDE_SIZE = CELL_SIDE_SIZE * GRID_SIDE_SIZE

TOP_COORD = 30.24268
LEFT_COORD = -88.77964
DOWN_COORD = 30.19767
RIGHT_COORD = -88.72648

##############################################
CELL_LAT = [DOWN_COORD + ((TOP_COORD - DOWN_COORD) * i) for i in range(GRID_SIDE_SIZE)]
CELL_LON = [LEFT_COORD + ((RIGHT_COORD - LEFT_COORD) * i) for i in range(GRID_SIDE_SIZE)]
##############################################