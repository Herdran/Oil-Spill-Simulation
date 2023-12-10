import os.path
import os.path
import re
import tkinter as tk
from tkinter import DISABLED, NORMAL, END, ANCHOR

import pandas as pd
from PIL import Image, ImageTk

from constatnts import set_simulation_coordinates_parameters
from files import get_main_path, get_data_path
from gui.utilities import create_frame, create_label_pack, create_label_grid, create_input_entry_grid, \
    create_label_grid_parameter_screen, browse_button, resize_img_to_fit_frame
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
            self.iter_as_sec = 20
            self.min_oil_thickness = 1
            self.oil_viscosity = 1
            self.oil_density = 1
            self.correctly_set_parameters = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
            self.img = None
            self.world_from_checkpoint = None
            self.oil_sources = []
            self.longitude_oil_source = 0.0
            self.latitude_oil_source = 0.0
            self.mass_per_minute_oil_source = 0.0
            self.spill_start_oil_source = "2010-04-01 00:00:00"
            self.spill_end_oil_source = "2010-04-02 00:00:00"
            self.correctly_set_parameters_oil_sources = [1, 1, 0, 1, 1]

            self.main_frame = create_frame(parent, 0, 0, 1, 1, tk.N + tk.S + tk.E + tk.W, 5, 5)

            self.main_frame.rowconfigure(0, weight=1, uniform='row')
            self.main_frame.rowconfigure(1, weight=1, uniform='row')
            self.main_frame.rowconfigure(2, weight=1, uniform='row')
            self.main_frame.rowconfigure(3, weight=1, uniform='row')
            self.main_frame.rowconfigure(4, weight=2, uniform='row')
            self.main_frame.rowconfigure(5, weight=2, uniform='row')
            self.main_frame.rowconfigure(6, weight=2, uniform='row')
            self.main_frame.rowconfigure(6, weight=1, uniform='row')
            self.main_frame.columnconfigure(0, weight=2, uniform='column')
            self.main_frame.columnconfigure(1, weight=2, uniform='column')
            self.main_frame.columnconfigure(2, weight=8, uniform='column')
            self.main_frame.columnconfigure(3, weight=1, uniform='column')

            title_frame = create_frame(self.main_frame, 0, 0, 1, 4, tk.N + tk.S)
            neighborhood_type_frame = create_frame(self.main_frame, 4, 0, 1, 1, tk.S + tk.W)
            inputs_frame = create_frame(self.main_frame, 1, 0, 3, 4, tk.N + tk.S + tk.W)
            data_path_frame = create_frame(self.main_frame, 5, 0, 1, 2, tk.S + tk.W)
            checkpoint_path_frame = create_frame(self.main_frame, 6, 0, 2, 2, tk.S + tk.W)
            confirm_and_start_frame = create_frame(self.main_frame, 7, 2, 1, 2, tk.S + tk.E)
            oil_sources_frame = create_frame(self.main_frame, 4, 1, 3, 2, tk.N + tk.S + tk.W)

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
            point_side_size_frame = create_frame(inputs_frame, 0, 4, 1, 1, tk.N + tk.S)
            time_per_iteration_frame = create_frame(inputs_frame, 1, 4, 1, 1, tk.N + tk.S)
            min_oil_thickness_frame = create_frame(inputs_frame, 2, 4, 1, 1, tk.N + tk.S)
            oil_viscosity_frame = create_frame(inputs_frame, 0, 5, 1, 1, tk.N + tk.S)
            oil_density_frame = create_frame(inputs_frame, 1, 5, 1, 1, tk.N + tk.S)

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
            create_label_grid(time_per_iteration_frame, "Time per iteration\n[s]")
            create_label_grid(min_oil_thickness_frame, "Minimum oil thickness\n[idk]")
            create_label_grid(oil_viscosity_frame, "Oil viscosity\n[idk]")
            create_label_grid(oil_density_frame, "Oil density\n[idk]")

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
            self.iter_as_sec_input = create_input_entry_grid(time_per_iteration_frame, 3, str(self.iter_as_sec),
                                                             self.validate_iter_as_sec)
            self.min_oil_thickness_input = create_input_entry_grid(min_oil_thickness_frame, 3, str(self.min_oil_thickness),
                                                             self.validate_min_oil_thickness)
            self.oil_viscosity_input = create_input_entry_grid(oil_viscosity_frame, 3, str(self.oil_viscosity),
                                                             self.validate_oil_viscosity)
            self.oil_density_input = create_input_entry_grid(oil_density_frame, 3, str(self.oil_density),
                                                             self.validate_oil_density)

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
            self.iter_as_sec_validation_label = create_label_grid_parameter_screen(time_per_iteration_frame)
            self.min_oil_thickness_validation_label = create_label_grid_parameter_screen(min_oil_thickness_frame)
            self.oil_viscosity_validation_label = create_label_grid_parameter_screen(oil_viscosity_frame)
            self.oil_density_validation_label = create_label_grid_parameter_screen(oil_density_frame)

            self.loaded_img = Image.open(os.path.join(get_main_path(), "data/Blue_Marble_2002.png"))

            self.map_view_frame = create_frame(inputs_frame, 0, 0, 4, 1, tk.N + tk.S, 3, 3)

            self.map_view = tk.Canvas(self.map_view_frame)

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

            create_label_grid(data_path_frame, "Data path:", font=("Arial", 14, "bold"), columnspan=2,
                              sticky=tk.N + tk.S + tk.W)

            browse_path_label = tk.Label(data_path_frame, textvariable=self.data_path)
            browse_path_label.grid(row=1, column=1, padx=3, pady=3, sticky=tk.N + tk.S + tk.W)

            data_path_browse = tk.Button(data_path_frame, text="Browse", command=lambda: browse_button(target=self.data_path))
            data_path_browse.grid(row=1, column=0, padx=3, pady=3, sticky=tk.N + tk.S + tk.W)

            create_label_grid(checkpoint_path_frame, "Checkpoint path:", font=("Arial", 14, "bold"), columnspan=2,
                              sticky=tk.N + tk.S + tk.W)

            self.checkpoint_path = tk.StringVar()

            browse_path_label = tk.Label(checkpoint_path_frame, textvariable=self.checkpoint_path)
            browse_path_label.grid(row=1, column=1, padx=3, pady=3, sticky=tk.N + tk.S + tk.W)

            data_path_browse = tk.Button(checkpoint_path_frame, text="Browse", command=self.browse_and_load_checkpoint)
            data_path_browse.grid(row=1, column=0, padx=3, pady=3, sticky=tk.N + tk.S + tk.W)

            self.confirm_and_continue = tk.Button(confirm_and_start_frame, text='Confirm and continue',
                                                  command=self.confirm_and_start_simulation)
            self.confirm_and_continue.pack(side=tk.RIGHT, padx=5, pady=5)


            # oil_sources_frame.rowconfigure(0, weight=1, uniform='row')
            # oil_sources_frame.rowconfigure(1, weight=4, uniform='row')
            # oil_sources_frame.rowconfigure(2, weight=1, uniform='row')
            # oil_sources_frame.rowconfigure(3, weight=5, uniform='row')
            # # oil_sources_frame.rowconfigure(4, weight=1, uniform='row')
            # # oil_sources_frame.rowconfigure(5, weight=1, uniform='row')
            # # oil_sources_frame.rowconfigure(6, weight=1, uniform='row')
            oil_sources_frame.columnconfigure(0, weight=1, uniform='column')
            oil_sources_frame.columnconfigure(1, weight=1, uniform='column')
            oil_sources_frame.columnconfigure(2, weight=1, uniform='column')
            oil_sources_frame.columnconfigure(3, weight=1, uniform='column')
            oil_sources_frame.columnconfigure(4, weight=1, uniform='column')
            # oil_sources_frame.columnconfigure(5, weight=1, uniform='column')

            # create_label_grid(oil_sources_frame, "Oil sources\n[latitude, longitude, kg/m, yyyy-mm-dd hh:mm:ss, yyyy-mm-dd hh:mm:ss]", columnspan=3)
            create_label_grid(oil_sources_frame, "Oil sources", columnspan=5)

            self.oil_sources_listbox = tk.Listbox(oil_sources_frame, width=100, height=7)

            self.oil_sources_listbox.grid(row=3, column=0, columnspan=5, sticky=tk.N + tk.S)
            # self.oil_sources_listbox.insert(END, "1")
            # self.oil_sources_listbox.insert(END, "2")
            # self.oil_sources_listbox.insert(END, "3")
            # self.oil_sources_listbox.insert(END, "4")
            # self.oil_sources_listbox.insert(END, "5")
            # self.oil_sources_listbox.insert(END, "6")

            self.oil_sources_listbox_insert = tk.Button(oil_sources_frame, text='Add',
                                                        command=self.insert_into_oil_sources_listbox)
            self.oil_sources_listbox_insert.grid(row=2, column=0, columnspan=2, sticky=tk.N + tk.S)

            self.oil_sources_listbox_delete = tk.Button(oil_sources_frame, text='Delete',
                                                        command=self.delete_from_oil_sources_listbox)
            self.oil_sources_listbox_delete.grid(row=2, column=3, columnspan=2, sticky=tk.N + tk.S)

            longitude_oil_source_frame = create_frame(oil_sources_frame, 1, 1, 1, 1, tk.N + tk.S)
            latitude_oil_source_frame = create_frame(oil_sources_frame, 1, 0, 1, 1, tk.N + tk.S)
            mass_per_minute_oil_source_frame = create_frame(oil_sources_frame, 1, 2, 1, 1, tk.N + tk.S)
            spill_start_oil_source_frame = create_frame(oil_sources_frame, 1, 3, 1, 1, tk.N + tk.S)
            spill_end_oil_source_frame = create_frame(oil_sources_frame, 1, 4, 1, 1, tk.N + tk.S)

            create_label_grid(longitude_oil_source_frame, "Latitude coord")
            create_label_grid(latitude_oil_source_frame, "Longitude coord")
            create_label_grid(mass_per_minute_oil_source_frame, "Mass per minute\n[idk, kg/m?]")  # TODO
            create_label_grid(spill_start_oil_source_frame, "Spill start\n[yyyy-mm-dd hh:mm:ss]")
            create_label_grid(spill_end_oil_source_frame, "Spill end\n[yyyy-mm-dd hh:mm:ss]")

            self.longitude_oil_source_input = create_input_entry_grid(longitude_oil_source_frame, 3, str(self.longitude_oil_source), self.validate_longitude_oil_source)
            self.latitude_oil_source_input = create_input_entry_grid(latitude_oil_source_frame, 3, str(self.latitude_oil_source), self.validate_latitude_oil_source)
            self.mass_per_minute_oil_source_input = create_input_entry_grid(mass_per_minute_oil_source_frame, 3, str(self.mass_per_minute_oil_source), self.validate_mass_per_minute_oil_source)
            self.spill_start_oil_source_input = create_input_entry_grid(spill_start_oil_source_frame, 17, self.spill_start_oil_source, self.validate_spill_start_oil_source)
            self.spill_end_oil_source_input = create_input_entry_grid(spill_end_oil_source_frame, 17, self.spill_end_oil_source, self.validate_spill_end_oil_source)

            self.longitude_oil_source_validation_label = create_label_grid_parameter_screen(longitude_oil_source_frame)
            self.latitude_oil_source_validation_label = create_label_grid_parameter_screen(latitude_oil_source_frame)
            self.mass_per_minute_oil_source_validation_label = create_label_grid_parameter_screen(mass_per_minute_oil_source_frame)
            self.spill_start_oil_source_validation_label = create_label_grid_parameter_screen(spill_start_oil_source_frame)
            self.spill_end_oil_source_validation_label = create_label_grid_parameter_screen(spill_end_oil_source_frame)

            self.map_view_frame.update()
            self.crop_and_resize_preview_image()
            self.main_frame.bind("<Configure>", self.resize_preview_image)
            self.validate_all_parameters()
            self.validate_all_parameters_oil_sources_listbox()

        def validate_coordinates_top(self, is_first_run=True):
            value = self.top_coord_input.get()
            if not value:
                return False
            if -90 <= float(value) <= 90 and float(value) > self.down_coord:
                self.top_coord = float(value)
                self.top_coord_validation_label.config(text="Valid value", fg="black")
                self.correctly_set_parameters[0] = 1
                self.check_all_parameters_validity_and_refresh_image(is_first_run)
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
                self.check_all_parameters_validity_and_refresh_image(is_first_run)
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
                self.check_all_parameters_validity_and_refresh_image(is_first_run)
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
                self.check_all_parameters_validity_and_refresh_image(is_first_run)
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

        def validate_iter_as_sec(self):
            value = self.iter_as_sec_input.get()
            if not value:
                return False
            try:
                if float(value) % 1 == 0 and float(value) > 0:
                    self.iter_as_sec = int(value)
                    self.iter_as_sec_validation_label.config(text="Valid value", fg="black")
                    self.correctly_set_parameters[10] = 1
                    self.check_all_parameters_validity_and_refresh_image()
                    return True
            except ValueError:
                pass
            self.iter_as_sec_validation_label.config(text="Invalid value", fg="red")
            self.confirm_and_continue.config(state=DISABLED)
            self.correctly_set_parameters[10] = 0

        def validate_min_oil_thickness(self):
            value = self.min_oil_thickness_input.get()
            if not value:
                return False
            try:
                if float(value) % 1 == 0 and float(value) > 0:  # TODO idk how to validate this value
                    self.iter_as_sec = int(value)
                    self.min_oil_thickness_validation_label.config(text="Valid value", fg="black")
                    self.correctly_set_parameters[11] = 1
                    self.check_all_parameters_validity_and_refresh_image()
                    return True
            except ValueError:
                pass
            self.min_oil_thickness_validation_label.config(text="Invalid value", fg="red")
            self.confirm_and_continue.config(state=DISABLED)
            self.correctly_set_parameters[11] = 0

        def validate_oil_viscosity(self):
            value = self.oil_viscosity_input.get()
            if not value:
                return False
            try:
                if float(value) % 1 == 0 and float(value) > 0:  # TODO idk how to validate this value
                    self.iter_as_sec = int(value)
                    self.oil_viscosity_validation_label.config(text="Valid value", fg="black")
                    self.correctly_set_parameters[12] = 1
                    self.check_all_parameters_validity_and_refresh_image()
                    return True
            except ValueError:
                pass
            self.oil_viscosity_validation_label.config(text="Invalid value", fg="red")
            self.confirm_and_continue.config(state=DISABLED)
            self.correctly_set_parameters[12] = 0

        def validate_oil_density(self):
            value = self.oil_density_input.get()
            if not value:
                return False
            try:
                if float(value) % 1 == 0 and float(value) > 0:  # TODO idk how to validate this value
                    self.iter_as_sec = int(value)
                    self.oil_density_validation_label.config(text="Valid value", fg="black")
                    self.correctly_set_parameters[13] = 1
                    self.check_all_parameters_validity_and_refresh_image()
                    return True
            except ValueError:
                pass
            self.oil_density_validation_label.config(text="Invalid value", fg="red")
            self.confirm_and_continue.config(state=DISABLED)
            self.correctly_set_parameters[13] = 0

        def validate_longitude_oil_source(self):
            value = self.longitude_oil_source_input.get()
            if not value:
                return False
            if -180 <= float(value) <= 180:
                self.longitude_oil_source = float(value)
                self.longitude_oil_source_validation_label.config(text="Valid value", fg="black")
                self.correctly_set_parameters_oil_sources[0] = 1
                self.check_all_parameters_validity_oil_sources()
                return True
            self.longitude_oil_source_validation_label.config(text="Invalid value", fg="red")
            self.oil_sources_listbox_insert.config(state=DISABLED)
            self.correctly_set_parameters_oil_sources[0] = 0

        def validate_latitude_oil_source(self):
            value = self.latitude_oil_source_input.get()
            if not value:
                return False
            if -90 <= float(value) <= 90:
                self.latitude_oil_source = float(value)
                self.latitude_oil_source_validation_label.config(text="Valid value", fg="black")
                self.correctly_set_parameters_oil_sources[1] = 1
                self.check_all_parameters_validity_oil_sources()
                return True
            self.latitude_oil_source_validation_label.config(text="Invalid value", fg="red")
            self.oil_sources_listbox_insert.config(state=DISABLED)
            self.correctly_set_parameters_oil_sources[1] = 0

        def validate_mass_per_minute_oil_source(self):
            value = self.mass_per_minute_oil_source_input.get()
            if not value:
                return False
            if float(value) > 0:
                self.mass_per_minute_oil_source = float(value)
                self.mass_per_minute_oil_source_validation_label.config(text="Valid value", fg="black")
                self.correctly_set_parameters_oil_sources[2] = 1
                self.check_all_parameters_validity_oil_sources()
                return True
            self.mass_per_minute_oil_source_validation_label.config(text="Invalid value", fg="red")
            self.oil_sources_listbox_insert.config(state=DISABLED)
            self.correctly_set_parameters_oil_sources[2] = 0

        def validate_spill_start_oil_source(self):
            value = self.spill_start_oil_source_input.get()
            if not value:
                return False
            if re.match('\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', value):
                try:
                    pd.Timestamp(value)
                    self.spill_start_oil_source = value
                    self.spill_start_oil_source_validation_label.config(text="Valid value", fg="black")
                    self.correctly_set_parameters_oil_sources[3] = 1
                    self.check_all_parameters_validity_oil_sources()
                    return True
                except ValueError:
                    pass
            self.spill_start_oil_source_validation_label.config(text="Invalid value", fg="red")
            self.oil_sources_listbox_insert.config(state=DISABLED)
            self.correctly_set_parameters_oil_sources[3] = 0

        def validate_spill_end_oil_source(self):
            value = self.spill_end_oil_source_input.get()
            if not value:
                return False
            if re.match('\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', value):
                try:
                    pd.Timestamp(value)
                    self.spill_end_oil_source = value
                    self.spill_end_oil_source_validation_label.config(text="Valid value", fg="black")
                    self.correctly_set_parameters_oil_sources[4] = 1
                    self.check_all_parameters_validity_oil_sources()
                    return True
                except ValueError:
                    pass
            self.spill_end_oil_source_validation_label.config(text="Invalid value", fg="red")
            self.oil_sources_listbox_insert.config(state=DISABLED)
            self.correctly_set_parameters_oil_sources[4] = 0

        def check_all_parameters_validity_oil_sources(self):
            if sum(self.correctly_set_parameters_oil_sources) == 5:
                self.oil_sources_listbox_insert.config(state=NORMAL)

        def validate_all_parameters(self):
            self.validate_coordinates_top(False)
            self.validate_coordinates_down(False)
            self.validate_coordinates_left(False)
            self.validate_coordinates_right(False)
            self.validate_time_range_start()
            self.validate_time_range_end()
            self.validate_data_time_step()
            self.validate_cells_side_count_latitude()
            self.validate_cells_side_count_longitude()
            self.validate_point_side_size()
            self.validate_iter_as_sec()
            self.validate_min_oil_thickness()
            self.validate_oil_viscosity()
            self.validate_oil_density()

        def validate_all_parameters_oil_sources_listbox(self):
            self.validate_latitude_oil_source()
            self.validate_longitude_oil_source()
            self.validate_mass_per_minute_oil_source()
            self.validate_spill_start_oil_source()
            self.validate_spill_end_oil_source()

        def check_all_parameters_validity_and_refresh_image(self, coordinate_change=False):
            if coordinate_change and sum(self.correctly_set_parameters[:4]) == 4:
                self.crop_and_resize_preview_image()
                if sum(self.correctly_set_parameters) == 14:
                    self.confirm_and_continue.config(state=NORMAL)

        def insert_into_oil_sources_listbox(self):
            self.oil_sources_listbox.insert(END, f"{self.latitude_oil_source}, "
                                                 f"{self.longitude_oil_source}, "
                                                 f"{self.mass_per_minute_oil_source}, "
                                                 f"{self.spill_start_oil_source}, "
                                                 f"{self.spill_end_oil_source}")

        def delete_from_oil_sources_listbox(self):
            self.oil_sources_listbox.delete(ANCHOR)

        def read_all_from_oil_sources_listbox(self):
            values = self.oil_sources_listbox.get(0, tk.END)
            for value in values:
                split_values = value.split(", ")
                self.oil_sources.append({"coord": (float(split_values[0]), float(split_values[1])),  #  TODO those values are not correct as they have geographical coordinates
                                       "mass_per_minute": float(split_values[2]),
                                       "spill_start": pd.Timestamp(split_values[3]),
                                       "spill_end": pd.Timestamp(split_values[4])})

        def browse_and_load_checkpoint(self):
            browse_button(self.checkpoint_path)
            if self.checkpoint_path:
                loaded_parameters = {}  # TODO load checkpoint here  # load_from_json(self.checkpoint_path, )
                self.set_all_parameters_from_checkpoint(loaded_parameters)
                self.validate_all_parameters()

        def set_all_parameters_from_checkpoint(self, loaded_parameters):
            pass
            # self.top_coord_input.setvar(loaded_parameters["top_coord"])
            # self.top_coord_input.config(state=DISABLED)
            # TODO etc

        def resize_preview_image(self, event=None):
            self.crop_and_resize_preview_image()

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
                                                  self.point_side_size,
                                                  self.iter_as_sec,
                                                  self.min_oil_thickness,
                                                  self.oil_viscosity,
                                                  self.oil_density
                                                  )

            self.read_all_from_oil_sources_listbox()
            start_simulation(Neighbourhood.MOORE if self.neighborhood_var.get() == 0 else Neighbourhood.VON_NEUMANN,
                             window, self.world_from_checkpoint, self.oil_sources)

        def crop_and_resize_preview_image(self):
            image_width, image_height = self.loaded_img.size

            nw_pixel_x = int((self.left_coord + 180) * (image_width / 360))
            nw_pixel_y = int((90 - self.top_coord) * (image_height / 180))

            se_pixel_x = int((self.right_coord + 180) * (image_width / 360))
            se_pixel_y = int((90 - self.down_coord) * (image_height / 180))

            # TODO Temporary measure in place for the view to actually show anything when the coordinates values are very similiar
            if nw_pixel_x + 10 >= se_pixel_x:
                nw_pixel_x -= 10
                se_pixel_x += 10
            if nw_pixel_y + 10 >= se_pixel_y:
                nw_pixel_y -= 10
                se_pixel_y += 10

            cropped_image = self.loaded_img.crop((nw_pixel_x, nw_pixel_y, se_pixel_x, se_pixel_y))

            resized_img = resize_img_to_fit_frame(cropped_image, self.map_view_frame)

            self.img = ImageTk.PhotoImage(resized_img)
            self.map_view.create_image(0, 0, image=self.img, anchor=tk.NW)

    ParametersSettingController(window)
