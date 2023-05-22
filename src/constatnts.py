POINT_SIDE_SIZE = 50  # [m]
CELL_SIDE_SIZE = 10  # points per cell side size
GRID_SIDE_SIZE = 10  # cells per grid side size
WORLD_SIDE_SIZE = CELL_SIDE_SIZE * GRID_SIDE_SIZE
ITER_AS_SEC = 20

TOP_COORD = 30.24268
LEFT_COORD = -88.77964
DOWN_COORD = 30.19767
RIGHT_COORD = -88.72648

CELL_LAT_SIZE = (TOP_COORD - DOWN_COORD)/GRID_SIDE_SIZE
CELL_LON_SIZE = (RIGHT_COORD - LEFT_COORD)/GRID_SIDE_SIZE

##############################################
CELL_LAT = [DOWN_COORD + CELL_LON_SIZE/2 + (CELL_LAT_SIZE * i) for i in range(GRID_SIDE_SIZE)]
CELL_LON = [LEFT_COORD + CELL_LON_SIZE/2 + (CELL_LON_SIZE * i) for i in range(GRID_SIDE_SIZE)]
##############################################
