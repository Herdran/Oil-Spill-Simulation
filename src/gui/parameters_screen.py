import re
import tkinter as tk
from tkinter import DISABLED, NORMAL, END, ANCHOR

import numpy as np
import pandas as pd
from PIL import Image, ImageTk

from checkpoints import load_from_json
from gui.main_screen import start_simulation
from gui.utilities import browse_dir_button, create_frame, create_label_pack, create_label_grid, create_input_entry_grid, \
    create_label_grid_parameter_screen, browse_button, resize_img_to_fit_frame
from initial_values import InitialValues
from initial_values_loader import set_simulation_coordinates_parameters
from simulation.utilities import Neighbourhood
from topology.file_loader import get_binary_scaled_map


def start_initial_menu(window):
    def set_text(input_widget, text):
        input_widget.delete(0, END)
        input_widget.insert(0, text)
        return

    class ParametersSettingController(tk.Frame):
        def __init__(self, parent):
            super().__init__(parent)
            self.top_coord = InitialValues.simulation_initial_parameters.area.max.latitude
            self.down_coord = InitialValues.simulation_initial_parameters.area.min.latitude
            self.left_coord = InitialValues.simulation_initial_parameters.area.min.longitude
            self.right_coord = InitialValues.simulation_initial_parameters.area.max.longitude
            self.time_range_start = str(InitialValues.simulation_initial_parameters.time.min)
            self.time_range_end = str(InitialValues.simulation_initial_parameters.time.max)
            self.data_time_step_minutes = int(
                InitialValues.simulation_initial_parameters.data_time_step.total_seconds() / 60)
            self.interpolation_grid_size_latitude = InitialValues.simulation_initial_parameters.interpolation_grid_size.latitude
            self.interpolation_grid_size_longitude = InitialValues.simulation_initial_parameters.interpolation_grid_size.longitude
            self.point_side_size = InitialValues.point_side_size
            self.iter_as_sec = InitialValues.iter_as_sec
            self.min_oil_thickness = InitialValues.min_oil_thickness
            self.oil_viscosity = InitialValues.viscosity_kinematic
            self.oil_density = InitialValues.oil_density
            self.checkpoint_frequency = InitialValues.checkpoint_frequency
            self.total_simulation_time = InitialValues.total_simulation_time
            self.curr_iter = InitialValues.curr_iter
            self.correctly_set_parameters = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
            self.img = None
            self.points_from_checkpoint = None
            self.oil_sources = []
            self.latitude_oil_source = 0.0
            self.longitude_oil_source = 0.0
            self.mass_per_minute_oil_source = 0.0
            self.spill_start_oil_source = str(InitialValues.simulation_initial_parameters.time.min)
            self.spill_end_oil_source = str(InitialValues.simulation_initial_parameters.time.max)
            self.correctly_set_parameters_oil_sources = [1, 1, 1, 1, 1]

            self.main_frame = create_frame(parent, 0, 0, 1, 1, tk.N + tk.S + tk.E + tk.W, 5, 5)

            self.main_frame.rowconfigure(0, weight=1, uniform='row')
            self.main_frame.rowconfigure(1, weight=2, uniform='row')
            self.main_frame.rowconfigure(2, weight=2, uniform='row')
            self.main_frame.rowconfigure(3, weight=2, uniform='row')
            self.main_frame.rowconfigure(4, weight=3, uniform='row')
            self.main_frame.rowconfigure(5, weight=2, uniform='row')
            self.main_frame.rowconfigure(6, weight=2, uniform='row')
            self.main_frame.rowconfigure(6, weight=1, uniform='row')
            self.main_frame.columnconfigure(0, weight=3, uniform='column')
            self.main_frame.columnconfigure(1, weight=2, uniform='column')
            self.main_frame.columnconfigure(2, weight=8, uniform='column')
            self.main_frame.columnconfigure(3, weight=1, uniform='column')

            title_frame = create_frame(self.main_frame, 0, 0, 1, 4, tk.N + tk.S)
            neighborhood_type_frame = create_frame(self.main_frame, 4, 0, 1, 1, tk.S + tk.W, relief_style=tk.RAISED,
                                                   padx=5, pady=5)
            inputs_frame = create_frame(self.main_frame, 1, 0, 3, 4, tk.N + tk.S, padx=5, pady=5)
            data_path_frame = create_frame(self.main_frame, 5, 0, 1, 2, tk.S + tk.W, relief_style=tk.RAISED, padx=3,
                                           pady=3)
            checkpoint_path_frame = create_frame(self.main_frame, 6, 0, 2, 2, tk.S + tk.W, relief_style=tk.RAISED,
                                                 padx=3, pady=3)
            confirm_and_start_frame = create_frame(self.main_frame, 7, 2, 1, 2, tk.S + tk.E)
            oil_sources_frame = create_frame(self.main_frame, 4, 1, 3, 2, tk.N + tk.S + tk.W, relief_style=tk.RAISED)

            create_label_pack(title_frame, "Oil Spill Simulation")

            inputs_frame.rowconfigure(0, weight=1, uniform='row')
            inputs_frame.rowconfigure(1, weight=1, uniform='row')
            inputs_frame.rowconfigure(2, weight=1, uniform='row')
            inputs_frame.columnconfigure(0, weight=1, uniform='column')
            inputs_frame.columnconfigure(1, weight=1, uniform='column')
            inputs_frame.columnconfigure(2, weight=1, uniform='column')
            inputs_frame.columnconfigure(3, weight=1, uniform='column')
            inputs_frame.columnconfigure(4, weight=1, uniform='column')
            inputs_frame.columnconfigure(5, weight=1, uniform='column')

            coord_and_time_range_frame = create_frame(inputs_frame, 0, 1, 3, 2, tk.N + tk.S, padx=3, pady=3)
            coord_frame = create_frame(coord_and_time_range_frame, 0, 1, 2, 2, tk.N + tk.S, relief_style=tk.RAISED)
            time_range_frame = create_frame(coord_and_time_range_frame, 2, 1, 1, 2, tk.N + tk.S, relief_style=tk.RAISED)
            data_processor_parameters_frame = create_frame(inputs_frame, 0, 3, 3, 1, tk.N + tk.S,
                                                           relief_style=tk.RAISED, padx=3, pady=3)
            other_parameters_frame = create_frame(inputs_frame, 0, 4, 3, 2, tk.N + tk.S, relief_style=tk.RAISED, padx=3,
                                                  pady=3)

            top_coord_frame = create_frame(coord_frame, 0, 0, 1, 1, tk.N + tk.S)
            down_coord_frame = create_frame(coord_frame, 1, 0, 1, 1, tk.N + tk.S)
            left_coord_frame = create_frame(coord_frame, 0, 1, 1, 1, tk.N + tk.S)
            right_coord_frame = create_frame(coord_frame, 1, 1, 1, 1, tk.N + tk.S)
            time_range_start_frame = create_frame(time_range_frame, 0, 0, 1, 1, tk.N + tk.S)
            time_range_end_frame = create_frame(time_range_frame, 0, 1, 1, 1, tk.N + tk.S)
            data_time_step_frame = create_frame(data_processor_parameters_frame, 2, 0, 1, 1, tk.N + tk.S)
            interpolation_grid_size_latitude_frame = create_frame(data_processor_parameters_frame, 0, 0, 1, 1,
                                                                  tk.N + tk.S)
            interpolation_grid_size_longitude_frame = create_frame(data_processor_parameters_frame, 1, 0, 1, 1,
                                                                   tk.N + tk.S)
            point_side_size_frame = create_frame(other_parameters_frame, 0, 0, 1, 1, tk.N + tk.S)
            time_per_iteration_frame = create_frame(other_parameters_frame, 1, 0, 1, 1, tk.N + tk.S)
            min_oil_thickness_frame = create_frame(other_parameters_frame, 2, 1, 1, 1, tk.N + tk.S)
            oil_viscosity_frame = create_frame(other_parameters_frame, 0, 1, 1, 1, tk.N + tk.S)
            oil_density_frame = create_frame(other_parameters_frame, 1, 1, 1, 1, tk.N + tk.S)
            checkpoint_frequency_frame = create_frame(other_parameters_frame, 2, 0, 1, 1, tk.N + tk.S)

            create_label_grid(top_coord_frame, "Top coord value\n[latitude]")
            create_label_grid(down_coord_frame, "Bottom coord value\n[latitude]")
            create_label_grid(left_coord_frame, "Left coord value\n[longitude]")
            create_label_grid(right_coord_frame, "Right coord value\n[longitude]")
            create_label_grid(time_range_start_frame, "Time range: start\n[yyyy-mm-dd hh:mm:ss]")
            create_label_grid(time_range_end_frame, "Time range: end\n[yyyy-mm-dd hh:mm:ss]")
            create_label_grid(data_time_step_frame, "Data time step\n[min]")
            create_label_grid(interpolation_grid_size_latitude_frame, "Data stations count:\nlatitude")
            create_label_grid(interpolation_grid_size_longitude_frame, "Data stations count:\nlongitude")
            create_label_grid(point_side_size_frame, "Point side size\n[m]")
            create_label_grid(time_per_iteration_frame, "Time per iteration\n[s]")
            create_label_grid(min_oil_thickness_frame, "Minimum oil thickness\n[μm]")
            create_label_grid(oil_viscosity_frame, "Oil kinematic viscosity\n[m^2/s]")
            create_label_grid(oil_density_frame, "Oil density\n[kg/m^3]")
            create_label_grid(checkpoint_frequency_frame, "Checkpoint frequency\n[per iterations]")

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
            self.interpolation_grid_size_latitude_input = create_input_entry_grid(
                interpolation_grid_size_latitude_frame, 3,
                str(self.interpolation_grid_size_latitude),
                self.validate_interpolation_grid_size_latitude)
            self.interpolation_grid_size_longitude_input = create_input_entry_grid(
                interpolation_grid_size_longitude_frame, 3,
                str(self.interpolation_grid_size_longitude),
                self.validate_interpolation_grid_size_longitude)
            self.point_side_size_input = create_input_entry_grid(point_side_size_frame, 3, str(self.point_side_size),
                                                                 self.validate_point_side_size)
            self.iter_as_sec_input = create_input_entry_grid(time_per_iteration_frame, 3, str(self.iter_as_sec),
                                                             self.validate_iter_as_sec)
            self.min_oil_thickness_input = create_input_entry_grid(min_oil_thickness_frame, 7,
                                                                   str(self.min_oil_thickness),
                                                                   self.validate_min_oil_thickness)
            self.oil_viscosity_input = create_input_entry_grid(oil_viscosity_frame, 7, str(self.oil_viscosity),
                                                               self.validate_oil_viscosity)
            self.oil_density_input = create_input_entry_grid(oil_density_frame, 7, str(self.oil_density),
                                                             self.validate_oil_density)
            self.checkpoint_frequency_input = create_input_entry_grid(checkpoint_frequency_frame, 7,
                                                                      str(self.checkpoint_frequency),
                                                                      self.validate_checkpoint_frequency)

            self.top_coord_validation_label = create_label_grid_parameter_screen(top_coord_frame)
            self.down_coord_validation_label = create_label_grid_parameter_screen(down_coord_frame)
            self.left_coord_validation_label = create_label_grid_parameter_screen(left_coord_frame)
            self.right_coord_validation_label = create_label_grid_parameter_screen(right_coord_frame)
            self.time_range_start_validation_label = create_label_grid_parameter_screen(time_range_start_frame)
            self.time_range_end_validation_label = create_label_grid_parameter_screen(time_range_end_frame)
            self.data_time_step_validation_label = create_label_grid_parameter_screen(data_time_step_frame)
            self.interpolation_grid_size_latitude_validation_label = create_label_grid_parameter_screen(
                interpolation_grid_size_latitude_frame)
            self.interpolation_grid_size_longitude_validation_label = create_label_grid_parameter_screen(
                interpolation_grid_size_longitude_frame)
            self.point_side_size_validation_label = create_label_grid_parameter_screen(point_side_size_frame)
            self.iter_as_sec_validation_label = create_label_grid_parameter_screen(time_per_iteration_frame)
            self.min_oil_thickness_validation_label = create_label_grid_parameter_screen(min_oil_thickness_frame)
            self.oil_viscosity_validation_label = create_label_grid_parameter_screen(oil_viscosity_frame)
            self.oil_density_validation_label = create_label_grid_parameter_screen(oil_density_frame)
            self.checkpoint_frequency_validation_label = create_label_grid_parameter_screen(checkpoint_frequency_frame)

            binary_map = np.array(get_binary_scaled_map()).reshape(
                InitialValues.BINARY_MAP_HEIGHT // InitialValues.PREVIEW_MAP_SCALE,
                InitialValues.BINARY_MAP_WIDTH // InitialValues.PREVIEW_MAP_SCALE)

            sea_color = np.array(InitialValues.SEA_COLOR, dtype=np.uint8)
            land_color = np.array(InitialValues.LAND_COLOR, dtype=np.uint8)
            self.loaded_img = np.where(binary_map[:, :, None] == 1, sea_color, land_color)

            self.loaded_img = Image.fromarray(self.loaded_img)

            self.map_view_frame = create_frame(inputs_frame, 0, 0, 3, 1, tk.N + tk.S, 3, 3)

            self.map_view = tk.Canvas(self.map_view_frame)

            self.map_view.grid(row=0, column=0, rowspan=3, padx=3, pady=3, sticky=tk.N + tk.S)

            create_label_grid(neighborhood_type_frame, "Neighborhood type:", font=("Arial", 14, "bold"))

            self.neighborhood_var = tk.IntVar()
            self.nm = tk.Radiobutton(neighborhood_type_frame, text="Moore", variable=self.neighborhood_var, value=0)
            self.nvm = tk.Radiobutton(neighborhood_type_frame, text="Von Neumann", variable=self.neighborhood_var,
                                      value=1)
            self.nm.select()

            self.nm.grid(row=1, column=0, rowspan=1, padx=3, pady=3, sticky=tk.N + tk.S)
            self.nvm.grid(row=2, column=0, rowspan=1, padx=3, pady=3, sticky=tk.N + tk.S)

            self.data_path = tk.StringVar()
            self.data_path.set(InitialValues.data_dir_path)

            create_label_grid(data_path_frame, "Data path:", font=("Arial", 14, "bold"), columnspan=2,
                              sticky=tk.N + tk.S + tk.W)

            browse_path_label = tk.Label(data_path_frame, textvariable=self.data_path)
            browse_path_label.grid(row=1, column=1, padx=3, pady=3, sticky=tk.N + tk.S + tk.W)

            data_path_browse = tk.Button(data_path_frame, text="Browse",
                                         command=lambda: browse_dir_button(target=self.data_path))
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

            oil_sources_frame.columnconfigure(0, weight=4, uniform='column')
            oil_sources_frame.columnconfigure(1, weight=4, uniform='column')
            oil_sources_frame.columnconfigure(2, weight=4, uniform='column')
            oil_sources_frame.columnconfigure(3, weight=5, uniform='column')
            oil_sources_frame.columnconfigure(4, weight=5, uniform='column')

            create_label_grid(oil_sources_frame, "Oil sources", columnspan=5)

            self.oil_sources_listbox = tk.Listbox(oil_sources_frame, width=95, height=3)

            self.oil_sources_listbox.grid(row=3, column=1, columnspan=3, sticky=tk.N + tk.S + tk.W, padx=5, pady=5)

            self.oil_sources_listbox_insert = tk.Button(oil_sources_frame, text='Add',
                                                        command=self.insert_into_oil_sources_listbox)
            self.oil_sources_listbox_insert.grid(row=2, column=0, columnspan=2, sticky=tk.N + tk.S)

            scrollbar = tk.Scrollbar(oil_sources_frame, command=self.oil_sources_listbox.yview)
            scrollbar.grid(row=3, column=4, sticky=tk.N + tk.S + tk.W, padx=5, pady=5)
            self.oil_sources_listbox.config(yscrollcommand=scrollbar.set)

            self.oil_sources_listbox_delete = tk.Button(oil_sources_frame, text='Delete',
                                                        command=self.delete_from_oil_sources_listbox)
            self.oil_sources_listbox_delete.grid(row=2, column=3, columnspan=2, sticky=tk.N + tk.S)

            latitude_oil_source_frame = create_frame(oil_sources_frame, 1, 0, 1, 1, tk.N + tk.S)
            longitude_oil_source_frame = create_frame(oil_sources_frame, 1, 1, 1, 1, tk.N + tk.S)
            mass_per_minute_oil_source_frame = create_frame(oil_sources_frame, 1, 2, 1, 1, tk.N + tk.S)
            spill_start_oil_source_frame = create_frame(oil_sources_frame, 1, 3, 1, 1, tk.N + tk.S)
            spill_end_oil_source_frame = create_frame(oil_sources_frame, 1, 4, 1, 1, tk.N + tk.S)

            create_label_grid(latitude_oil_source_frame, "Latitude coord\n")
            create_label_grid(longitude_oil_source_frame, "Longitude coord\n")
            create_label_grid(mass_per_minute_oil_source_frame, "Mass per minute\n[kg/min]")
            create_label_grid(spill_start_oil_source_frame, "Spill start\n[yyyy-mm-dd hh:mm:ss]")
            create_label_grid(spill_end_oil_source_frame, "Spill end\n[yyyy-mm-dd hh:mm:ss]")

            self.latitude_oil_source_input = create_input_entry_grid(latitude_oil_source_frame, 9,
                                                                     str(self.latitude_oil_source),
                                                                     self.validate_latitude_oil_source)
            self.longitude_oil_source_input = create_input_entry_grid(longitude_oil_source_frame, 9,
                                                                      str(self.longitude_oil_source),
                                                                      self.validate_longitude_oil_source)
            self.mass_per_minute_oil_source_input = create_input_entry_grid(mass_per_minute_oil_source_frame, 7,
                                                                            str(self.mass_per_minute_oil_source),
                                                                            self.validate_mass_per_minute_oil_source)
            self.spill_start_oil_source_input = create_input_entry_grid(spill_start_oil_source_frame, 17,
                                                                        self.spill_start_oil_source,
                                                                        self.validate_spill_start_oil_source)
            self.spill_end_oil_source_input = create_input_entry_grid(spill_end_oil_source_frame, 17,
                                                                      self.spill_end_oil_source,
                                                                      self.validate_spill_end_oil_source)

            self.longitude_oil_source_validation_label = create_label_grid_parameter_screen(longitude_oil_source_frame)
            self.latitude_oil_source_validation_label = create_label_grid_parameter_screen(latitude_oil_source_frame)
            self.mass_per_minute_oil_source_validation_label = create_label_grid_parameter_screen(
                mass_per_minute_oil_source_frame)
            self.spill_start_oil_source_validation_label = create_label_grid_parameter_screen(
                spill_start_oil_source_frame)
            self.spill_end_oil_source_validation_label = create_label_grid_parameter_screen(spill_end_oil_source_frame)

            self.map_view_frame.update()
            self.crop_and_resize_preview_image()
            self.main_frame.bind("<Configure>", self.crop_and_resize_preview_image)
            self.validate_all_parameters()
            self.validate_all_parameters_oil_sources_listbox()

        def validate_coordinates_top(self, is_first_run=True):
            value = self.top_coord_input.get()
            if not value:
                return False
            try:
                if -90 <= float(value) <= 90 and float(value) > self.down_coord:
                    self.top_coord = float(value)
                    self.top_coord_validation_label.config(text="Valid value", fg="black")
                    self.correctly_set_parameters[0] = 1
                    self.check_all_main_parameters_validity(is_first_run)
                    if is_first_run:
                        self.validate_coordinates_down(False)
                    return True
            except ValueError:
                pass
            self.top_coord_validation_label.config(text="Invalid value", fg="red")
            self.confirm_and_continue.config(state=DISABLED)
            self.correctly_set_parameters[0] = 0

        def validate_coordinates_down(self, is_first_run=True):
            value = self.down_coord_input.get()
            if not value:
                return False
            try:
                if -90 <= float(value) <= 90 and float(value) < self.top_coord:
                    self.down_coord = float(value)
                    self.down_coord_validation_label.config(text="Valid value", fg="black")
                    self.correctly_set_parameters[1] = 1
                    self.check_all_main_parameters_validity(is_first_run)
                    if is_first_run:
                        self.validate_coordinates_top(False)
                    return True
            except ValueError:
                pass
            self.down_coord_validation_label.config(text="Invalid value", fg="red")
            self.confirm_and_continue.config(state=DISABLED)
            self.correctly_set_parameters[1] = 0

        def validate_coordinates_left(self, is_first_run=True):
            value = self.left_coord_input.get()
            if not value:
                return False
            try:
                if -180 <= float(value) <= 180 and float(value) < self.right_coord:
                    self.left_coord = float(value)
                    self.left_coord_validation_label.config(text="Valid value", fg="black")
                    self.correctly_set_parameters[2] = 1
                    self.check_all_main_parameters_validity(is_first_run)
                    if is_first_run:
                        self.validate_coordinates_right(False)
                    return True
            except ValueError:
                pass
            self.left_coord_validation_label.config(text="Invalid value", fg="red")
            self.confirm_and_continue.config(state=DISABLED)
            self.correctly_set_parameters[2] = 0

        def validate_coordinates_right(self, is_first_run=True):
            value = self.right_coord_input.get()
            if not value:
                return False
            try:
                if -180 <= float(value) <= 180 and float(value) > self.left_coord:
                    self.right_coord = float(value)
                    self.right_coord_validation_label.config(text="Valid value", fg="black")
                    self.correctly_set_parameters[3] = 1
                    self.check_all_main_parameters_validity(is_first_run)
                    if is_first_run:
                        self.validate_coordinates_left(False)
                    return True
            except ValueError:
                pass
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
                    self.check_all_main_parameters_validity()
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
                    self.check_all_main_parameters_validity()
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
                    self.check_all_main_parameters_validity()
                    return True
            except ValueError:
                pass
            self.data_time_step_validation_label.config(text="Invalid value", fg="red")
            self.confirm_and_continue.config(state=DISABLED)
            self.correctly_set_parameters[6] = 0

        def validate_interpolation_grid_size_latitude(self):
            value = self.interpolation_grid_size_latitude_input.get()
            if not value:
                return False
            try:
                if float(value) % 1 == 0 and float(
                        value) > 0:
                    self.interpolation_grid_size_latitude = int(value)
                    self.interpolation_grid_size_latitude_validation_label.config(text="Valid value", fg="black")
                    self.correctly_set_parameters[7] = 1
                    self.check_all_main_parameters_validity()
                    return True
            except ValueError:
                pass
            self.interpolation_grid_size_latitude_validation_label.config(text="Invalid value", fg="red")
            self.confirm_and_continue.config(state=DISABLED)
            self.correctly_set_parameters[7] = 0

        def validate_interpolation_grid_size_longitude(self):
            value = self.interpolation_grid_size_longitude_input.get()
            if not value:
                return False
            try:
                if float(value) % 1 == 0 and float(
                        value) > 0:
                    self.interpolation_grid_size_longitude = int(value)
                    self.interpolation_grid_size_longitude_validation_label.config(text="Valid value", fg="black")
                    self.correctly_set_parameters[8] = 1
                    self.check_all_main_parameters_validity()
                    return True
            except ValueError:
                pass
            self.interpolation_grid_size_longitude_validation_label.config(text="Invalid value", fg="red")
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
                    self.check_all_main_parameters_validity()
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
                    self.check_all_main_parameters_validity()
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
                if float(value) > 0:
                    self.min_oil_thickness = float(value)
                    self.min_oil_thickness_validation_label.config(text="Valid value", fg="black")
                    self.correctly_set_parameters[11] = 1
                    self.check_all_main_parameters_validity()
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
                if float(value) > 0:
                    self.oil_viscosity = float(value)
                    self.oil_viscosity_validation_label.config(text="Valid value", fg="black")
                    self.correctly_set_parameters[12] = 1
                    self.check_all_main_parameters_validity()
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
                if float(value) > 0:
                    self.oil_density = float(value)
                    self.oil_density_validation_label.config(text="Valid value", fg="black")
                    self.correctly_set_parameters[13] = 1
                    self.check_all_main_parameters_validity()
                    return True
            except ValueError:
                pass
            self.oil_density_validation_label.config(text="Invalid value", fg="red")
            self.confirm_and_continue.config(state=DISABLED)
            self.correctly_set_parameters[13] = 0

        def validate_checkpoint_frequency(self):
            value = self.checkpoint_frequency_input.get()
            if not value:
                return False
            try:
                if float(value) % 1 == 0 and float(value) >= 0:
                    self.checkpoint_frequency = int(value)
                    self.checkpoint_frequency_validation_label.config(text="Valid value", fg="black")
                    self.correctly_set_parameters[14] = 1
                    self.check_all_main_parameters_validity()
                    return True
            except ValueError:
                pass
            self.checkpoint_frequency_validation_label.config(text="Invalid value", fg="red")
            self.confirm_and_continue.config(state=DISABLED)
            self.correctly_set_parameters[14] = 0

        def validate_longitude_oil_source(self):
            value = self.longitude_oil_source_input.get()
            if not value:
                return False
            try:
                if self.left_coord <= float(value) <= self.right_coord:
                    self.longitude_oil_source = float(value)
                    self.longitude_oil_source_validation_label.config(text="Valid value", fg="black")
                    self.correctly_set_parameters_oil_sources[0] = 1
                    self.check_all_oil_sources_parameters_validity()
                    return True
            except ValueError:
                pass
            self.longitude_oil_source_validation_label.config(text="Invalid value", fg="red")
            self.oil_sources_listbox_insert.config(state=DISABLED)
            self.correctly_set_parameters_oil_sources[0] = 0

        def validate_latitude_oil_source(self):
            value = self.latitude_oil_source_input.get()
            if not value:
                return False
            try:
                if self.down_coord <= float(value) <= self.top_coord:
                    self.latitude_oil_source = float(value)
                    self.latitude_oil_source_validation_label.config(text="Valid value", fg="black")
                    self.correctly_set_parameters_oil_sources[1] = 1
                    self.check_all_oil_sources_parameters_validity()
                    return True
            except ValueError:
                pass
            self.latitude_oil_source_validation_label.config(text="Invalid value", fg="red")
            self.oil_sources_listbox_insert.config(state=DISABLED)
            self.correctly_set_parameters_oil_sources[1] = 0

        def validate_mass_per_minute_oil_source(self):
            value = self.mass_per_minute_oil_source_input.get()
            if not value:
                return False
            try:
                if float(value) > 0:
                    self.mass_per_minute_oil_source = float(value)
                    self.mass_per_minute_oil_source_validation_label.config(text="Valid value", fg="black")
                    self.correctly_set_parameters_oil_sources[2] = 1
                    self.check_all_oil_sources_parameters_validity()
                    return True
            except ValueError:
                pass
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
                    self.check_all_oil_sources_parameters_validity()
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
                    self.check_all_oil_sources_parameters_validity()
                    return True
                except ValueError:
                    pass
            self.spill_end_oil_source_validation_label.config(text="Invalid value", fg="red")
            self.oil_sources_listbox_insert.config(state=DISABLED)
            self.correctly_set_parameters_oil_sources[4] = 0

        def check_all_oil_sources_parameters_validity(self):
            if all(self.correctly_set_parameters_oil_sources):
                self.oil_sources_listbox_insert.config(state=NORMAL)

        def validate_all_parameters(self):
            self.validate_coordinates_top(False)
            self.validate_coordinates_down(False)
            self.validate_coordinates_left(False)
            self.validate_coordinates_right(False)
            self.validate_time_range_start()
            self.validate_time_range_end()
            self.validate_data_time_step()
            self.validate_interpolation_grid_size_latitude()
            self.validate_interpolation_grid_size_longitude()
            self.validate_point_side_size()
            self.validate_iter_as_sec()
            self.validate_min_oil_thickness()
            self.validate_oil_viscosity()
            self.validate_oil_density()
            self.validate_checkpoint_frequency()

        def validate_all_parameters_oil_sources_listbox(self):
            self.validate_latitude_oil_source()
            self.validate_longitude_oil_source()
            self.validate_mass_per_minute_oil_source()
            self.validate_spill_start_oil_source()
            self.validate_spill_end_oil_source()

        def check_all_main_parameters_validity(self, coordinate_change=False):
            if coordinate_change and sum(self.correctly_set_parameters[:4]) == 4:
                self.crop_and_resize_preview_image()
                if all(self.correctly_set_parameters):
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
                self.oil_sources.append({"coord": (float(split_values[0]), float(split_values[1])),
                                         "mass_per_minute": float(split_values[2]),
                                         "spill_start": pd.Timestamp(split_values[3]),
                                         "spill_end": pd.Timestamp(split_values[4])})

        def browse_and_load_checkpoint(self):
            browse_button(self.checkpoint_path)
            if self.checkpoint_path.get():
                loaded_parameters = load_from_json(self.checkpoint_path.get())
                self.set_all_parameters_from_checkpoint(loaded_parameters)
                self.validate_all_parameters()
                self.set_initial_time()
                self.check_all_main_parameters_validity(True)
                
        def set_initial_time(self):
            SECONDS_IN_MINUTE = 60
            total_simulation_time_second_offset = self.total_simulation_time % SECONDS_IN_MINUTE
            total_simulation_time_minutes = int(self.total_simulation_time / SECONDS_IN_MINUTE)
            offset_after_last_weather_minutes = total_simulation_time_minutes % self.data_time_step_minutes
            data_preprocessor_initial_seconds = self.total_simulation_time - (offset_after_last_weather_minutes * SECONDS_IN_MINUTE) + total_simulation_time_second_offset
            data_preprocessor_initial_timestamp = pd.Timestamp(self.time_range_start) + pd.Timedelta(seconds=data_preprocessor_initial_seconds)
            InitialValues.data_preprocessor_initial_timestamp = data_preprocessor_initial_timestamp     

        def set_all_parameters_from_checkpoint(self, loaded_parameters):
            set_text(self.top_coord_input, str(loaded_parameters["top_coord"]))
            self.top_coord_input.config(state=DISABLED)
            set_text(self.down_coord_input, str(loaded_parameters["down_coord"]))
            self.down_coord_input.config(state=DISABLED)
            set_text(self.left_coord_input, str(loaded_parameters["left_coord"]))
            self.left_coord_input.config(state=DISABLED)
            set_text(self.right_coord_input, str(loaded_parameters["right_coord"]))
            self.right_coord_input.config(state=DISABLED)
            set_text(self.time_range_start_input, str(loaded_parameters["time_range_start"]))
            self.time_range_start_input.config(state=DISABLED)
            set_text(self.time_range_end_input, str(loaded_parameters["time_range_end"]))
            self.time_range_end_input.config(state=DISABLED)
            set_text(self.data_time_step_input, str(loaded_parameters["data_time_step"]))
            self.data_time_step_input.config(state=DISABLED)
            set_text(self.interpolation_grid_size_latitude_input, str(loaded_parameters["cells_side_count_latitude"]))
            self.interpolation_grid_size_latitude_input.config(state=DISABLED)
            set_text(self.interpolation_grid_size_longitude_input, str(loaded_parameters["cells_side_count_longitude"]))
            self.interpolation_grid_size_longitude_input.config(state=DISABLED)
            set_text(self.point_side_size_input, str(loaded_parameters["point_side_size"]))
            self.point_side_size_input.config(state=DISABLED)
            set_text(self.iter_as_sec_input, str(loaded_parameters["iter_as_sec"]))
            self.iter_as_sec_input.config(state=DISABLED)
            set_text(self.min_oil_thickness_input, str(loaded_parameters["min_oil_thickness"]))
            self.min_oil_thickness_input.config(state=DISABLED)
            set_text(self.oil_viscosity_input, str(loaded_parameters["oil_viscosity"]))
            self.oil_viscosity_input.config(state=DISABLED)
            set_text(self.oil_density_input, str(loaded_parameters["oil_density"]))
            self.oil_density_input.config(state=DISABLED)
            set_text(self.checkpoint_frequency_input, str(loaded_parameters["checkpoint_frequency"]))
            self.checkpoint_frequency_input.config(state=DISABLED)

            self.total_simulation_time = loaded_parameters["total_simulation_time"]
            self.curr_iter = loaded_parameters["curr_iter"]
            self.points_from_checkpoint = loaded_parameters["points"]
            self.checkpoint_frequency = loaded_parameters["checkpoint_frequency"]

            self.data_path.set(loaded_parameters["data_path"])

            self.nm.config(state=DISABLED)
            self.nvm.config(state=DISABLED)

            if loaded_parameters["neighborhood"] == "Neighbourhood.MOORE":
                self.nm.select()
                self.neighborhood_var.set(0)
            else:
                self.nvm.select()
                self.neighborhood_var.set(1)

            for oil_source in loaded_parameters["constant_sources"]:
                self.oil_sources_listbox.insert(END, f"{oil_source[0][0]}, "
                                                     f"{oil_source[0][1]}, "
                                                     f"{oil_source[1]}, "
                                                     f"{oil_source[2]}, "
                                                     f"{oil_source[3]}")

            self.longitude_oil_source_input.config(state=DISABLED)
            self.latitude_oil_source_input.config(state=DISABLED)
            self.mass_per_minute_oil_source_input.config(state=DISABLED)
            self.spill_start_oil_source_input.config(state=DISABLED)
            self.spill_end_oil_source_input.config(state=DISABLED)
            self.oil_sources_listbox_insert.config(state=DISABLED)
            self.oil_sources_listbox_delete.config(state=DISABLED)
                    
        def crop_and_resize_preview_image(self, event=None):
            image_width, image_height = self.loaded_img.size

            nw_pixel_x = int((self.left_coord + 180) * (image_width / 360))
            nw_pixel_y = int((90 - self.top_coord) * (image_height / 180))

            se_pixel_x = int((self.right_coord + 180) * (image_width / 360))
            se_pixel_y = int((90 - self.down_coord) * (image_height / 180))

            cropped_image = self.loaded_img.crop((nw_pixel_x, nw_pixel_y, se_pixel_x, se_pixel_y))

            resized_img = resize_img_to_fit_frame(cropped_image, self.map_view_frame)

            self.img = ImageTk.PhotoImage(resized_img)
            self.map_view.create_image(0, 0, image=self.img, anchor=tk.NW)

        def confirm_and_start_simulation(self):
            self.confirm_and_continue.config(state=DISABLED)
            set_simulation_coordinates_parameters(self.top_coord,
                                                  self.down_coord,
                                                  self.left_coord,
                                                  self.right_coord,
                                                  self.time_range_start,
                                                  self.time_range_end,
                                                  self.data_time_step_minutes,
                                                  self.interpolation_grid_size_latitude,
                                                  self.interpolation_grid_size_longitude,
                                                  self.data_path.get(),
                                                  self.point_side_size,
                                                  self.iter_as_sec,
                                                  self.min_oil_thickness,
                                                  self.oil_viscosity,
                                                  self.oil_density,
                                                  Neighbourhood.MOORE if self.neighborhood_var.get() == 0
                                                  else Neighbourhood.VON_NEUMANN,
                                                  self.checkpoint_frequency,
                                                  self.total_simulation_time,
                                                  self.curr_iter
                                                  )

            self.read_all_from_oil_sources_listbox()
            start_simulation(window, self.points_from_checkpoint, self.oil_sources)

    ParametersSettingController(window)
