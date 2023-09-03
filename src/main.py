import cProfile
import os
import time
from pathlib import Path
from random import randint

import gui
import simulation.simulation as simulation
from constatnts import SIMULATION_INITIAL_PARAMETERS, POINTS_SIDE_COUNT
from data.data_processor import DataProcessor, DataReader, DataValidationException

if __name__ == "__main__":
    # gui.run()
    # cProfile.run('gui.run()')

    def get_data_processor() -> DataProcessor:
        sym_data_reader = DataReader()

        try:
            path = Path("data/test_data")
            if os.getcwd().endswith('src'):
                path = os.path.join('..', path)
            sym_data_reader.add_all_from_dir(path)
        except DataValidationException as ex:
            # TODO: some kind of error popup?
            print("Error with Data Validation: ", ex)
            exit(1)

        return sym_data_reader.preprocess(SIMULATION_INITIAL_PARAMETERS)


    engine = simulation.SimulationEngine(get_data_processor())

    # points_with_oil_num = 5
    oil_per_click = 100000000

    for i in range(0, POINTS_SIDE_COUNT):
        for j in range(0, POINTS_SIDE_COUNT):
            coord = (i, j)
            if coord not in engine.lands:
                engine.world[coord] = simulation.Point(coord, engine.initial_values, engine)
                point_clicked = engine.world[coord]
                point_clicked.add_oil(oil_per_click)

    # for i in range(1, points_with_oil_num + 1):
    #     coord = None
    #     while coord is None or coord in engine.lands or coord in engine.world:
    #         coord = (randint(0, POINTS_SIDE_COUNT - 1), randint(0, POINTS_SIDE_COUNT - 1))
    #
    #     engine.world[coord] = simulation.Point(coord, engine.initial_values, engine)
    #     point_clicked = engine.world[coord]
    #     point_clicked.add_oil(oil_per_click)

    time_elapsed_sum = 0
    iteration_num = 1000

    for i in range(iteration_num):
        start = time.time()
        engine.update(20)
        end = time.time()
        elapsed_time = end - start
        time_elapsed_sum += elapsed_time
        print(f"Iterartion: {i}, Time elapsed: {elapsed_time}s, Number of currently active points: {len(engine.world)}")

    print(f"\n\nAverage time elapsed after {iteration_num} iterations: {time_elapsed_sum / iteration_num}s")
