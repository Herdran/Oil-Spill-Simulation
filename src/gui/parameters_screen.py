import os.path
import os.path
import re
import tkinter as tk
from tkinter import DISABLED, NORMAL, filedialog

import pandas as pd
from PIL import Image, ImageTk

from constatnts import set_simulation_coordinates_parameters
from files import get_main_path, get_data_path
from gui.utilities import create_frame, create_label_pack, create_label_grid, create_input_entry_grid, \
    create_label_grid_parameter_screen
from gui.main_screen import start_simulation
from simulation.utilities import Neighbourhood


def start_initial_menu(window):
    class ParametersSettingController(tk.Frame):
        def __init__(self, parent):
            super().__init__(parent)
            self.top_coord = 30.24268
            self.down_coord = 30.19767
            self.left_coord = -88.77964
            self.right_coord = -88.72648
            self.time_range_start = "2010-04-01 00:00:00"
            self.time_range_end = "2010-04-02 00:00:00"
            self.data_time_step_minutes = 30
            self.cells_side_count_latitude = 10
            self.cells_side_count_longitude = 10
            self.point_side_size = 50
            self.correctly_set_parameters = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
            self.img = None

            self.main_frame = create_frame(parent, 0, 0, 1, 1, tk.N + tk.S + tk.E + tk.W, 5, 5)

            self.main_frame.rowconfigure(0, weight=2, uniform='row')
            self.main_frame.rowconfigure(1, weight=1, uniform='row')
            self.main_frame.rowconfigure(2, weight=1, uniform='row')
            self.main_frame.rowconfigure(3, weight=1, uniform='row')
            self.main_frame.rowconfigure(4, weight=2, uniform='row')
            self.main_frame.rowconfigure(5, weight=2, uniform='row')
            self.main_frame.columnconfigure(0, weight=2, uniform='column')
            self.main_frame.columnconfigure(1, weight=3, uniform='column')
            self.main_frame.columnconfigure(2, weight=1, uniform='column')

            title_frame = create_frame(self.main_frame, 0, 0, 1, 3, tk.N + tk.S)
            neighborhood_type_frame = create_frame(self.main_frame, 4, 0, 1, 1, tk.S + tk.W)
            inputs_frame = create_frame(self.main_frame, 1, 0, 3, 3, tk.N + tk.S + tk.W)
            data_path_frame = create_frame(self.main_frame, 5, 0, 1, 3, tk.S + tk.W)
            confirm_and_start_frame = create_frame(self.main_frame, 5, 2, 1, 1, tk.S + tk.E)

            create_label_pack(title_frame, "Oil Spill Simulation")

            inputs_frame.rowconfigure(0, weight=1, uniform='row')
            inputs_frame.rowconfigure(1, weight=1, uniform='row')
            inputs_frame.rowconfigure(2, weight=1, uniform='row')
            inputs_frame.columnconfigure(0, weight=5, uniform='column')
            inputs_frame.columnconfigure(1, weight=3, uniform='column')
            inputs_frame.columnconfigure(2, weight=3, uniform='column')
            inputs_frame.columnconfigure(3, weight=3, uniform='column')
            inputs_frame.columnconfigure(4, weight=3, uniform='column')

            top_coord_frame = create_frame(inputs_frame, 0, 1, 1, 1, tk.N + tk.S)
            down_coord_frame = create_frame(inputs_frame, 1, 1, 1, 1, tk.N + tk.S)
            left_coord_frame = create_frame(inputs_frame, 0, 2, 1, 1, tk.N + tk.S)
            right_coord_frame = create_frame(inputs_frame, 1, 2, 1, 1, tk.N + tk.S)
            time_range_start_frame = create_frame(inputs_frame, 2, 1, 1, 1, tk.N + tk.S)
            time_range_end_frame = create_frame(inputs_frame, 2, 2, 1, 1, tk.N + tk.S)
            data_time_step_frame = create_frame(inputs_frame, 2, 3, 1, 1, tk.N + tk.S)
            cells_side_count_latitude_frame = create_frame(inputs_frame, 0, 3, 1, 1, tk.N + tk.S)
            cells_side_count_longitude_frame = create_frame(inputs_frame, 1, 3, 1, 1, tk.N + tk.S)
            point_side_size_frame = create_frame(inputs_frame, 1, 4, 1, 1, tk.N + tk.S)

            create_label_grid(top_coord_frame, "Top coord value\n[latitude]")
            create_label_grid(down_coord_frame, "Bottom coord value\n[latitude]")
            create_label_grid(left_coord_frame, "Left coord value\n[longitude]")
            create_label_grid(right_coord_frame, "Right coord value\n[longitude]")
            create_label_grid(time_range_start_frame, "Time range: start\n[yyyy-mm-dd hh:mm:ss]")
            create_label_grid(time_range_end_frame, "Time range: end\n[yyyy-mm-dd hh:mm:ss]")
            create_label_grid(data_time_step_frame, "Data time step\n[min]")
            create_label_grid(cells_side_count_latitude_frame, "Data stations count:\nlatitude")
            create_label_grid(cells_side_count_longitude_frame, "Data stations count:\nlongitude")
            create_label_grid(point_side_size_frame, "Point side size\n[m]")

            self.top_coord_input = create_input_entry_grid(top_coord_frame, 9, str(self.top_coord),
                                                           self.validate_coordinates_top)
            self.down_coord_input = create_input_entry_grid(down_coord_frame, 9, str(self.down_coord),
                                                            self.validate_coordinates_down)
            self.left_coord_input = create_input_entry_grid(left_coord_frame, 9, str(self.left_coord),
                                                            self.validate_coordinates_left)
            self.right_coord_input = create_input_entry_grid(right_coord_frame, 9, str(self.right_coord),
                                                             self.validate_coordinates_right)
            self.time_range_start_input = create_input_entry_grid(time_range_start_frame, 17,
                                                                  str(self.time_range_start),
                                                                  self.validate_time_range_start)
            self.time_range_end_input = create_input_entry_grid(time_range_end_frame, 17, str(self.time_range_end),
                                                                self.validate_time_range_end)
            self.data_time_step_input = create_input_entry_grid(data_time_step_frame, 3,
                                                                str(self.data_time_step_minutes),
                                                                self.validate_data_time_step)
            self.cells_side_count_latitude_input = create_input_entry_grid(cells_side_count_latitude_frame, 3,
                                                                           str(self.cells_side_count_latitude),
                                                                           self.validate_cells_side_count_latitude)
            self.cells_side_count_longitude_input = create_input_entry_grid(cells_side_count_longitude_frame, 3,
                                                                            str(self.cells_side_count_longitude),
                                                                            self.validate_cells_side_count_longitude)
            self.point_side_size_input = create_input_entry_grid(point_side_size_frame, 3, str(self.point_side_size),
                                                                 self.validate_point_side_size)

            self.top_coord_validation_label = create_label_grid_parameter_screen(top_coord_frame)
            self.down_coord_validation_label = create_label_grid_parameter_screen(down_coord_frame)
            self.left_coord_validation_label = create_label_grid_parameter_screen(left_coord_frame)
            self.right_coord_validation_label = create_label_grid_parameter_screen(right_coord_frame)
            self.time_range_start_validation_label = create_label_grid_parameter_screen(time_range_start_frame)
            self.time_range_end_validation_label = create_label_grid_parameter_screen(time_range_end_frame)
            self.data_time_step_validation_label = create_label_grid_parameter_screen(data_time_step_frame)
            self.cells_side_count_latitude_validation_label = create_label_grid_parameter_screen(cells_side_count_latitude_frame)
            self.cells_side_count_longitude_validation_label = create_label_grid_parameter_screen(cells_side_count_longitude_frame)
            self.point_side_size_validation_label = create_label_grid_parameter_screen(point_side_size_frame)

            self.loaded_img = Image.open(os.path.join(get_main_path(), "data/Blue_Marble_2002.png"))

            self.map_view_frame = create_frame(inputs_frame, 0, 0, 4, 1, tk.N + tk.S, 3, 3)

            self.map_view = tk.Canvas(self.map_view_frame)
            self.load_and_crop_image()

            self.map_view.grid(row=0, column=0, rowspan=3, padx=3, pady=3, sticky=tk.N + tk.S)

            create_label_grid(neighborhood_type_frame, "Neighborhood type:", font=("Arial", 14, "bold"))

            self.neighborhood_var = tk.IntVar()
            nm = tk.Radiobutton(neighborhood_type_frame, text="Moore", variable=self.neighborhood_var, value=0)
            nvm = tk.Radiobutton(neighborhood_type_frame, text="Von Neumann", variable=self.neighborhood_var, value=1)
            nm.select()

            nm.grid(row=1, column=0, rowspan=1, padx=3, pady=3, sticky=tk.N + tk.S)
            nvm.grid(row=2, column=0, rowspan=1, padx=3, pady=3, sticky=tk.N + tk.S)

            self.data_path = tk.StringVar()
            self.data_path.set(get_data_path())

            create_label_grid(data_path_frame, "Neighborhood type:", font=("Arial", 14, "bold"), columnspan=2,
                              sticky=tk.N + tk.S + tk.W)

            browse_path_label = tk.Label(data_path_frame, textvariable=self.data_path)
            browse_path_label.grid(row=1, column=1, padx=3, pady=3, sticky=tk.N + tk.S + tk.W)

            data_path_browse = tk.Button(data_path_frame, text="Browse", command=self.browse_button)
            data_path_browse.grid(row=1, column=0, padx=3, pady=3, sticky=tk.N + tk.S + tk.W)

            self.confirm_and_continue = tk.Button(confirm_and_start_frame, text='Confirm and continue',
                                                  command=self.confirm_and_start_simulation)
            self.confirm_and_continue.pack(side=tk.RIGHT, padx=5, pady=5)

            self.validate_all_parameters()

        def validate_coordinates_top(self, is_first_run=True):
            value = self.top_coord_input.get()
            if not value:
                return False
            if -90 <= float(value) <= 90 and float(value) > self.down_coord:
                self.top_coord = float(value)
                self.top_coord_validation_label.config(text="Valid value", fg="black")
                self.correctly_set_parameters[0] = 1
                self.check_all_parameters_validity_and_refresh_image()
                if is_first_run:
                    self.validate_coordinates_down(False)
                return True
            self.top_coord_validation_label.config(text="Invalid value", fg="red")
            self.confirm_and_continue.config(state=DISABLED)
            self.correctly_set_parameters[0] = 0

        def validate_coordinates_down(self, is_first_run=True):
            value = self.down_coord_input.get()
            if not value:
                return False
            if -90 <= float(value) <= 90 and float(value) < self.top_coord:
                self.down_coord = float(value)
                self.down_coord_validation_label.config(text="Valid value", fg="black")
                self.correctly_set_parameters[1] = 1
                self.check_all_parameters_validity_and_refresh_image()
                if is_first_run:
                    self.validate_coordinates_top(False)
                return True
            self.down_coord_validation_label.config(text="Invalid value", fg="red")
            self.confirm_and_continue.config(state=DISABLED)
            self.correctly_set_parameters[1] = 0

        def validate_coordinates_left(self, is_first_run=True):
            value = self.left_coord_input.get()
            if not value:
                return False
            if -180 <= float(value) <= 180 and float(value) < self.right_coord:
                self.left_coord = float(value)
                self.left_coord_validation_label.config(text="Valid value", fg="black")
                self.correctly_set_parameters[2] = 1
                self.check_all_parameters_validity_and_refresh_image()
                if is_first_run:
                    self.validate_coordinates_right(False)
                return True
            self.left_coord_validation_label.config(text="Invalid value", fg="red")
            self.confirm_and_continue.config(state=DISABLED)
            self.correctly_set_parameters[2] = 0

        def validate_coordinates_right(self, is_first_run=True):
            value = self.right_coord_input.get()
            if not value:
                return False
            if -180 <= float(value) <= 180 and float(value) > self.left_coord:
                self.right_coord = float(value)
                self.right_coord_validation_label.config(text="Valid value", fg="black")
                self.correctly_set_parameters[3] = 1
                self.check_all_parameters_validity_and_refresh_image()
                if is_first_run:
                    self.validate_coordinates_left(False)
                return True
            self.right_coord_validation_label.config(text="Invalid value", fg="red")
            self.confirm_and_continue.config(state=DISABLED)
            self.correctly_set_parameters[3] = 0

        def validate_time_range_start(self):
            value = self.time_range_start_input.get()
            if not value:
                return False
            if re.match('\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', value):
                try:
                    pd.Timestamp(value)
                    self.time_range_start = value
                    self.time_range_start_validation_label.config(text="Valid value", fg="black")
                    self.correctly_set_parameters[4] = 1
                    self.check_all_parameters_validity_and_refresh_image()
                    return True
                except ValueError:
                    pass
            self.time_range_start_validation_label.config(text="Invalid value", fg="red")
            self.confirm_and_continue.config(state=DISABLED)
            self.correctly_set_parameters[4] = 0

        def validate_time_range_end(self):
            value = self.time_range_end_input.get()
            if not value:
                return False
            if re.match('\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', value):
                try:
                    pd.Timestamp(value)
                    self.time_range_end = value
                    self.time_range_end_validation_label.config(text="Valid value", fg="black")
                    self.correctly_set_parameters[5] = 1
                    self.check_all_parameters_validity_and_refresh_image()
                    return True
                except ValueError:
                    pass
            self.time_range_end_validation_label.config(text="Invalid value", fg="red")
            self.confirm_and_continue.config(state=DISABLED)
            self.correctly_set_parameters[5] = 0

        def validate_data_time_step(self):
            value = self.data_time_step_input.get()
            if not value:
                return False
            try:
                if float(value) % 1 == 0:
                    self.data_time_step_minutes = int(value)
                    self.data_time_step_validation_label.config(text="Valid value", fg="black")
                    self.correctly_set_parameters[6] = 1
                    self.check_all_parameters_validity_and_refresh_image()
                    return True
            except ValueError:
                pass
            self.data_time_step_validation_label.config(text="Invalid value", fg="red")
            self.confirm_and_continue.config(state=DISABLED)
            self.correctly_set_parameters[6] = 0

        def validate_cells_side_count_latitude(self):
            value = self.cells_side_count_latitude_input.get()
            if not value:
                return False
            try:
                if float(value) % 1 == 0 and float(
                        value) > 0:
                    self.cells_side_count_latitude = int(value)
                    self.cells_side_count_latitude_validation_label.config(text="Valid value", fg="black")
                    self.correctly_set_parameters[7] = 1
                    self.check_all_parameters_validity_and_refresh_image()
                    return True
            except ValueError:
                pass
            self.cells_side_count_latitude_validation_label.config(text="Invalid value", fg="red")
            self.confirm_and_continue.config(state=DISABLED)
            self.correctly_set_parameters[7] = 0

        def validate_cells_side_count_longitude(self):
            value = self.cells_side_count_longitude_input.get()
            if not value:
                return False
            try:
                if float(value) % 1 == 0 and float(
                        value) > 0:
                    self.cells_side_count_longitude = int(value)
                    self.cells_side_count_longitude_validation_label.config(text="Valid value", fg="black")
                    self.correctly_set_parameters[8] = 1
                    self.check_all_parameters_validity_and_refresh_image()
                    return True
            except ValueError:
                pass
            self.cells_side_count_longitude_validation_label.config(text="Invalid value", fg="red")
            self.confirm_and_continue.config(state=DISABLED)
            self.correctly_set_parameters[8] = 0

        def validate_point_side_size(self):
            value = self.point_side_size_input.get()
            if not value:
                return False
            try:
                if float(value) % 1 == 0 and float(value) > 0:
                    self.point_side_size = int(value)
                    self.point_side_size_validation_label.config(text="Valid value", fg="black")
                    self.correctly_set_parameters[9] = 1
                    self.check_all_parameters_validity_and_refresh_image()
                    return True
            except ValueError:
                pass
            self.point_side_size_validation_label.config(text="Invalid value", fg="red")
            self.confirm_and_continue.config(state=DISABLED)
            self.correctly_set_parameters[9] = 0

        def validate_all_parameters(self):
            self.validate_coordinates_top()
            self.validate_coordinates_down()
            self.validate_coordinates_left()
            self.validate_coordinates_right()
            self.validate_time_range_start()
            self.validate_time_range_end()
            self.validate_data_time_step()
            self.validate_cells_side_count_latitude()
            self.validate_cells_side_count_longitude()
            self.validate_point_side_size()

        def check_all_parameters_validity_and_refresh_image(self):
            if sum(self.correctly_set_parameters[:4]) == 4:
                self.load_and_crop_image()
                if sum(self.correctly_set_parameters) == 10:
                    self.confirm_and_continue.config(state=NORMAL)

        def browse_button(self):
            filename = filedialog.askdirectory()
            if filename:
                self.data_path.set(filename)

        def confirm_and_start_simulation(self):
            set_simulation_coordinates_parameters(self.top_coord,
                                                  self.down_coord,
                                                  self.left_coord,
                                                  self.right_coord,
                                                  self.time_range_start,
                                                  self.time_range_end,
                                                  self.data_time_step_minutes,
                                                  self.cells_side_count_latitude,
                                                  self.cells_side_count_longitude,
                                                  self.data_path.get(),
                                                  self.point_side_size
                                                  )

            start_simulation(Neighbourhood.MOORE if self.neighborhood_var.get() == 0 else Neighbourhood.VON_NEUMANN,
                             window)

        def load_and_crop_image(self):
            w, h = self.loaded_img.size

            longitude_west_bound = int(w * (self.left_coord + 180) / 360)
            longitude_east_bound = int(w * (self.right_coord + 180) / 360)
            latitude_upper_bound = int(h * -(self.top_coord - 90) / 180)
            latitude_lower_bound = int(h * -(self.down_coord - 90) / 180)

            # TODO Temporary measure in place for the view to actually show anything when the coordinates values are very similiar
            if longitude_west_bound + 10 >= longitude_east_bound:
                longitude_west_bound -= 10
                longitude_east_bound += 10
            if latitude_upper_bound + 10 >= latitude_lower_bound:
                latitude_lower_bound += 10
                latitude_upper_bound -= 10

            cropped_img = self.loaded_img.crop(
                (longitude_west_bound, latitude_upper_bound, longitude_east_bound, latitude_lower_bound))

            w, h = cropped_img.size

            if w >= h and h / w < 0.5:
                w_resize = 400
                h_resize = int(400 * (h / w))
            else:
                h_resize = 200
                w_resize = int(200 * (w / h))

            resized_img = cropped_img.resize((w_resize, h_resize))

            self.img = ImageTk.PhotoImage(resized_img)
            self.map_view.create_image(0, 0, image=self.img, anchor=tk.NW)

    ParametersSettingController(window)
