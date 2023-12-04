import logging
import os.path
import tkinter as tk
from tkinter import DISABLED, NORMAL, filedialog
import re

import numpy as np
import threading

import pandas as pd
from PIL import Image, ImageTk

import simulation.simulation as simulation
from simulation.utilities import Neighbourhood
from data.data_processor import DataProcessor, DataReader, DataValidationException
from data.utilities import kelvins_to_celsius
from color import rgba, blend_color, rgba_to_rgb
from files import get_main_path, get_data_path
from constatnts import Constants as const, set_simulation_coordinates_parameters


def get_tooltip_text(point: simulation.Point) -> str:
    return f"""Oil mass: {point.oil_mass: .2f}kg
--------------------
Wind speed N: {point.wind_velocity[0]: .2f}m/s
Wind speed E: {point.wind_velocity[1]: .2f}m/s
Current speed N: {point.wave_velocity[0]: .2f}m/s
Current speed E: {point.wave_velocity[1]: .2f}m/s
Temperature: {kelvins_to_celsius(point.temperature): .2f}°C"""


def run():
    def start_simulation(neighborhood):
        SEA_COLOR = rgba(15, 10, 222)
        LAND_COLOR = rgba(38, 166, 91)
        OIL_COLOR = rgba(0, 0, 0)
        LAND_WITH_OIL_COLOR = rgba(0, 100, 0)

        class ImageViewer(tk.Canvas):
            def __init__(self, parent, image_array, image_change_controller, initial_zoom_level):
                super().__init__(parent)
                self.image_array = image_array
                self.image_array_height, self.image_array_width, _ = self.image_array.shape
                self.current_image = None
                self.initial_zoom_level = initial_zoom_level
                self.zoom_level = initial_zoom_level
                self.zoomed_width = int(image_array.shape[1] * initial_zoom_level)
                self.zoomed_height = int(image_array.shape[0] * initial_zoom_level)
                self.image_id = None
                self.prev_x = 0
                self.prev_y = 0
                self.pan_x = 0
                self.pan_y = 0
                self.is_holding = None
                self.is_panning = None
                self.tooltip = None
                self.img = None
                self.image_change_controller = image_change_controller

                self.bind("<MouseWheel>", self.on_mousewheel)
                self.bind("<ButtonPress-1>", self.on_button_press)
                self.bind("<B1-Motion>", self.on_button_motion)
                self.bind("<ButtonRelease-1>", self.on_button_release)
                self.bind("<Motion>", self.on_motion)
                self.bind("<Leave>", self.on_leave)

                self.bind("<Configure>", self.resize)

            def update_image(self):
                self.zoomed_width = int(self.image_array_width * self.zoom_level)
                self.zoomed_height = int(self.image_array_height * self.zoom_level)

                window_width = self.winfo_width()
                window_height = self.winfo_height()

                self.pan_x = max(min(self.pan_x, 0), min(window_width - self.zoomed_width, 0))
                self.pan_y = max(min(self.pan_y, 0), min(window_height - self.zoomed_height, 0))

                image_array = self.image_array[
                              int(-self.pan_y / self.zoom_level):
                              int(window_height / self.zoom_level - (self.pan_y / self.zoom_level)),
                              int(-self.pan_x / self.zoom_level):
                              int(window_width / self.zoom_level - (self.pan_x / self.zoom_level))
                              ]
                # TODO slicing image array has to be proportional to the original proportions of the image to retain readability
                #  and allow for rectangle images

                self.img = Image.fromarray(image_array)
                self.img = self.img.resize((min(window_width, self.zoomed_width),
                                            min(window_height, self.zoomed_height)),
                                           Image.NEAREST)

                self.current_image = ImageTk.PhotoImage(self.img)
                self.image_id = self.create_image(max(0, (window_width - self.zoomed_width) // 2),
                                                  max(0, (window_height - self.zoomed_height) // 2),
                                                  anchor=tk.NW,
                                                  image=self.current_image)

            def on_mousewheel(self, event):
                zoom_factor = 1.1 if event.delta > 0 else 10 / 11

                window_width = self.winfo_width()
                window_height = self.winfo_height()

                before_x = (self.image_array_width - (window_width / self.zoom_level))
                before_y = (self.image_array_height - (window_height / self.zoom_level))

                self.zoom_level *= zoom_factor
                self.zoom_level = min(max(self.zoom_level, self.initial_zoom_level), 100)

                if event.delta > 0:
                    self.pan_x -= max((((self.image_array_width - (window_width / self.zoom_level)) - before_x) / 2) * self.zoom_level, 0)
                    self.pan_y -= max((((self.image_array_height - (window_height / self.zoom_level)) - before_y) / 2) * self.zoom_level, 0)
                else:
                    self.pan_x += max(((before_x - (self.image_array_width - (window_width / self.zoom_level))) / 2) * self.zoom_level, 0)
                    self.pan_y += max(((before_y - (self.image_array_height - (window_height / self.zoom_level))) / 2) * self.zoom_level, 0)

                shift_x = event.x / window_width - 0.5
                shift_y = event.y / window_height - 0.5

                self.pan_x -= shift_x * window_width
                self.pan_y -= shift_y * window_height

                self.update_image()
                self.image_change_controller.update_zoom_infobox_value()

            def on_button_press(self, event):
                self.prev_x = event.x
                self.prev_y = event.y
                self.is_holding = True

            def on_button_release(self, event):
                self.is_holding = False
                if self.is_panning:
                    self.is_panning = False
                elif self.image_change_controller.oil_spill_on_bool:
                    window_width = self.winfo_width()
                    window_height = self.winfo_height()
                    x = int((event.x - self.pan_x - max((window_width - self.zoomed_width) // 2, 0)) / self.zoom_level)
                    y = int((event.y - self.pan_y - max((window_height - self.zoomed_height) // 2, 0)) / self.zoom_level)
                    if 0 <= x < self.image_array.shape[1] and 0 <= y < self.image_array.shape[0]:
                        coord = (x, y)
                        if coord not in engine.lands:
                            if coord not in engine.world:
                                engine.world[coord] = simulation.Point(coord, engine.initial_values, engine)
                            point_clicked = engine.world[coord]
                            point_clicked.add_oil(self.image_change_controller.oil_to_add_on_click)

                            var = blend_color(OIL_COLOR, SEA_COLOR,
                                              point_clicked.oil_mass / self.image_change_controller.minimal_oil_to_show,
                                              True)
                            self.image_change_controller.update_infobox()
                            image_array[y][x] = var[:3]
                            self.update_image()
                            self.show_tooltip(event.x_root, event.y_root, get_tooltip_text(point_clicked))
                            self.image_change_controller.value_not_yet_processed += self.image_change_controller.oil_to_add_on_click
                    self.image_change_controller.update_oil_amount_infobox()

            def on_button_motion(self, event):
                if self.is_holding:
                    self.is_panning = True
                    delta_x = event.x - self.prev_x
                    delta_y = event.y - self.prev_y
                    self.pan_x += delta_x
                    self.pan_y += delta_y
                    self.prev_x = event.x
                    self.prev_y = event.y
                    self.update_image()
                    if self.tooltip:
                        self.tooltip.update_position(event.x_root, event.y_root)

            def on_motion(self, event):
                window_width = self.winfo_width()
                window_height = self.winfo_height()
                x = int((event.x - self.pan_x - max((window_width - self.zoomed_width) // 2, 0)) / self.zoom_level)
                y = int((event.y - self.pan_y - max((window_height - self.zoomed_height) // 2, 0)) / self.zoom_level)
                coord = (x, y)
                if 0 <= x < self.image_array.shape[1] and 0 <= y < self.image_array.shape[0]:
                    if coord not in engine.world:
                        self.show_tooltip(event.x_root, event.y_root, f"Oil mass: {0: .2f}kg")
                    else:
                        point = engine.world[(x, y)]
                        self.show_tooltip(event.x_root, event.y_root, get_tooltip_text(point))
                else:
                    self.hide_tooltip()

            def on_leave(self, _):
                self.hide_tooltip()

            def show_tooltip(self, x, y, text):
                if self.tooltip is None:
                    self.tooltip = ToolTip(self, x, y, text)
                else:
                    self.tooltip.update_text(text)
                    self.tooltip.update_position(x, y)

            def hide_tooltip(self):
                if self.tooltip is not None:
                    self.tooltip.hide()

            def resize(self, event=None):
                window_width = self.winfo_width()
                window_height = self.winfo_height()
                self.zoom_level /= self.initial_zoom_level
                self.initial_zoom_level = min(window_width / image_array.shape[1], window_height / image_array.shape[0])
                self.zoom_level *= self.initial_zoom_level
                self.update_image()

        class ToolTip:
            def __init__(self, parent, x, y, text):
                self.parent = parent
                self.text = text
                self.tooltip_window = tk.Toplevel(parent)
                self.tooltip_label = tk.Label(
                    self.tooltip_window,
                    text=text,
                    background="#ffffe0",
                    relief=tk.SOLID,
                    borderwidth=1,
                )
                self.tooltip_label.pack()
                self.tooltip_window.wm_overrideredirect(True)
                self.tooltip_window.wm_geometry(f"+{x + 15}+{y + 10}")
                self.tooltip_window.attributes("-topmost", True)

            def update_text(self, text):
                self.tooltip_label.config(text=text)

            def update_position(self, x, y):
                self.tooltip_window.wm_geometry(f"+{x + 15}+{y + 10}")

            def hide(self):
                self.tooltip_window.destroy()
                self.parent.tooltip = None

        class ImageChangeController(tk.Frame):
            def __init__(self, parent, image_array):
                super().__init__(parent)
                self.image_array = image_array
                self.is_running = False
                self.interval = 10
                self.job_id = None
                self.is_updating = False
                self.curr_iter = 0
                self.sim_sec_passed = 0
                self.oil_to_add_on_click = 10000
                self.minimal_oil_to_show = 100
                self.iter_as_sec = const.ITER_AS_SEC
                self.viewer = None
                self.value_not_yet_processed = 0
                self.oil_spill_on_bool = True

                self.options_frame = tk.Frame(window)
                self.options_frame.grid(row=1, column=0, rowspan=1, columnspan=2,  padx=10, pady=10, sticky=tk.N + tk.S)

                self.options_frame.columnconfigure(0, weight=2)
                self.options_frame.columnconfigure(1, weight=2)
                self.options_frame.columnconfigure(2, weight=2)
                self.options_frame.columnconfigure(3, weight=2)
                self.options_frame.columnconfigure(4, weight=1)
                self.options_frame.columnconfigure(5, weight=1)

                interval_frame = tk.Frame(self.options_frame)
                iter_as_sec_frame = tk.Frame(self.options_frame)
                oil_added_frame = tk.Frame(self.options_frame)
                minimal_oil_value_to_show_frame = tk.Frame(self.options_frame)
                start_stop_frame = tk.Frame(self.options_frame)

                interval_frame.grid(row=0, column=0, rowspan=1, padx=10, pady=10, sticky=tk.N + tk.S)
                iter_as_sec_frame.grid(row=0, column=1, rowspan=1, padx=10, pady=10, sticky=tk.N + tk.S)
                oil_added_frame.grid(row=0, column=2, rowspan=1, padx=10, pady=10, sticky=tk.N + tk.S)
                minimal_oil_value_to_show_frame.grid(row=0, column=3, rowspan=1, padx=10, pady=10, sticky=tk.N + tk.S)
                start_stop_frame.grid(row=0, column=4, rowspan=1, columnspan=2, padx=10, pady=10, sticky=tk.N + tk.S)

                self.set_interval_label = tk.Label(interval_frame,
                                                   text="Interval of changes [s]",
                                                   font=("Arial", 14, "bold"), padx=10, pady=5)
                self.set_interval_label.pack(side=tk.TOP)
                self.set_iter_as_sec_label = tk.Label(iter_as_sec_frame,
                                                      text="Time per iteration [s]",
                                                      font=("Arial", 14, "bold"), padx=10, pady=5)
                self.set_iter_as_sec_label.pack(side=tk.TOP)
                self.set_oil_added_label = tk.Label(oil_added_frame,
                                                    text="Oil added on click [kg]",
                                                    font=("Arial", 14, "bold"), padx=10, pady=5)
                self.set_oil_added_label.pack(side=tk.TOP)
                self.oil_spill_on_var = tk.IntVar()
                self.set_oil_spill_on_off = tk.Checkbutton(oil_added_frame,
                                                           text="ON/OFF",
                                                           variable=self.oil_spill_on_var,
                                                           onvalue=1,
                                                           offvalue=0,
                                                           command=self.oil_spill_on_off)
                self.set_oil_spill_on_off.pack(side=tk.TOP)
                self.set_oil_spill_on_off.select()

                self.set_minimal_oil_value_to_show = tk.Label(minimal_oil_value_to_show_frame,
                                                              text="Minimal oil value to show [kg]",
                                                              font=("Arial", 14, "bold"), padx=10, pady=5)
                self.set_minimal_oil_value_to_show.pack(side=tk.TOP)

                self.btn_start_stop = tk.Button(start_stop_frame, text="Start", width=10, command=self.toggle_start_stop)
                self.btn_start_stop.pack(side=tk.TOP, padx=5, pady=5)

                self.text_interval = tk.Entry(interval_frame, width=10)
                self.text_interval.insert(tk.END, str(self.interval / 1000))
                self.text_interval.pack(side=tk.BOTTOM, padx=5, pady=5)
                self.text_interval.bind("<KeyPress>", self.on_key_press_interval)
                self.text_interval.bind("<FocusOut>", self.on_focus_out_interval)

                self.text_iter_as_sec = tk.Entry(iter_as_sec_frame, width=10)
                self.text_iter_as_sec.insert(tk.END, str(self.iter_as_sec))
                self.text_iter_as_sec.pack(side=tk.BOTTOM, padx=5, pady=5)
                self.text_iter_as_sec.bind("<KeyPress>", self.on_key_press_iter_as_sec)
                self.text_iter_as_sec.bind("<FocusOut>", self.on_focus_out_iter_as_sec)

                self.text_oil_added = tk.Entry(oil_added_frame, width=10)
                self.text_oil_added.insert(tk.END, str(self.oil_to_add_on_click))
                self.text_oil_added.pack(side=tk.BOTTOM, padx=5, pady=5)
                self.text_oil_added.bind("<KeyPress>", self.on_key_press_oil_to_add)
                self.text_oil_added.bind("<FocusOut>", self.on_focus_out_oil_to_add)

                self.text_minimal_oil_show = tk.Entry(minimal_oil_value_to_show_frame, width=10)
                self.text_minimal_oil_show.insert(tk.END, str(self.minimal_oil_to_show))
                self.text_minimal_oil_show.pack(side=tk.BOTTOM, padx=5, pady=5)
                self.text_minimal_oil_show.bind("<KeyPress>", self.on_key_press_oil_to_show)
                self.text_minimal_oil_show.bind("<FocusOut>", self.on_focus_out_oil_to_show)

                self.infoboxes_frame = tk.Frame(window)
                self.infoboxes_frame.grid(row=0, column=1, rowspan=1, columnspan=1, sticky=tk.N + tk.S + tk.E)

                frame_infoboxes_labels = tk.Frame(self.infoboxes_frame)

                frame_infoboxes_labels.grid(row=0, column=0, rowspan=1, padx=10, pady=10, sticky=tk.N + tk.S + tk.E)
                self.infobox1_labels_label = tk.Label(frame_infoboxes_labels, text="Current iteration",
                                                      font=("Arial", 14, "bold"), padx=10, pady=5)
                self.infobox1_labels_label.pack(side=tk.TOP)
                self.infobox2_labels_label = tk.Label(frame_infoboxes_labels, text="Simulation time",
                                                      font=("Arial", 14, "bold"), padx=10, pady=5)
                self.infobox2_labels_label.pack(side=tk.TOP)
                self.infobox3_labels_label = tk.Label(frame_infoboxes_labels, text="Global oil amount [sea]",
                                                      font=("Arial", 14, "bold"), padx=10, pady=5)
                self.infobox3_labels_label.pack(side=tk.TOP)
                self.infobox4_labels_label = tk.Label(frame_infoboxes_labels, text="Global oil amount [land]",
                                                      font=("Arial", 14, "bold"), padx=10, pady=5)
                self.infobox4_labels_label.pack(side=tk.TOP)
                self.infobox5_labels_label = tk.Label(frame_infoboxes_labels, text="Current zoom",
                                                      font=("Arial", 14, "bold"), padx=10, pady=5)
                self.infobox5_labels_label.pack(side=tk.TOP)

                frame_infoboxes_values = tk.Frame(self.infoboxes_frame)
                frame_infoboxes_values.grid(row=0, column=1, rowspan=1, padx=10, pady=10, sticky=tk.N + tk.S + tk.E)
                self.infobox1_values_label = tk.Label(frame_infoboxes_values, text="", font=("Arial", 14, "bold"), padx=10,
                                                      pady=5)
                self.infobox1_values_label.pack(side=tk.TOP)
                self.infobox2_values_label = tk.Label(frame_infoboxes_values, text="", font=("Arial", 14, "bold"), padx=10,
                                                      pady=5)
                self.infobox2_values_label.pack(side=tk.TOP)
                self.infobox3_values_label = tk.Label(frame_infoboxes_values, text="", font=("Arial", 14, "bold"), padx=10,
                                                      pady=5)
                self.infobox3_values_label.pack(side=tk.TOP)
                self.infobox4_values_label = tk.Label(frame_infoboxes_values, text="", font=("Arial", 14, "bold"), padx=10,
                                                      pady=5)
                self.infobox4_values_label.pack(side=tk.TOP)
                self.infobox5_values_label = tk.Label(frame_infoboxes_values, text="1.0", font=("Arial", 14, "bold"), padx=10,
                                                      pady=5)
                self.infobox5_values_label.pack(side=tk.TOP)
                
                self.bottom_frame = tk.Frame(window)
                self.bottom_frame.grid(row=1, column=0, rowspan=1, columnspan=2,  padx=10, pady=10, sticky=tk.N + tk.S)
                self.label_finished = tk.Label(self.bottom_frame,
                                                text="Simulation finished!",
                                                font=("Arial", 14, "bold"), padx=10, pady=5)
                
                self.label_finished.pack(side=tk.TOP)
                self.bottom_frame.grid_remove()

                self.update_image_array()
                self.update_infobox()

            def set_viewer(self, viewer):
                self.viewer = viewer

            def on_key_press_interval(self, event):
                if event.keysym == "Return":
                    self.validate_interval()

            def on_focus_out_interval(self, _):
                self.validate_interval()

            def on_key_press_iter_as_sec(self, event):
                if event.keysym == "Return":
                    self.validate_iter_as_sec()

            def on_focus_out_iter_as_sec(self, _):
                self.validate_iter_as_sec()

            def on_key_press_oil_to_add(self, event):
                if event.keysym == "Return":
                    self.validate_oil_to_add()

            def on_focus_out_oil_to_add(self, _):
                self.validate_oil_to_add()

            def on_key_press_oil_to_show(self, event):
                if event.keysym == "Return":
                    self.validate_minimal_oil_to_show()

            def on_focus_out_oil_to_show(self, _):
                self.validate_minimal_oil_to_show()

            def validate_interval(self):
                new_value = self.text_interval.get()
                try:
                    interval = float(new_value)
                    interval = max(0.01, min(2.0, interval))
                    self.interval = int(interval * 1000)
                    self.text_interval.delete(0, tk.END)
                    self.text_interval.insert(tk.END, str(interval))
                    if self.is_running:
                        self.after_cancel(self.job_id)
                        self.job_id = self.after(self.interval, threading.Thread(target=self.update_image_array).start())
                except ValueError:
                    pass

            def validate_iter_as_sec(self):
                new_value = self.text_iter_as_sec.get()
                try:
                    iter_as_sec = int(new_value)
                    iter_as_sec = max(1, iter_as_sec)
                    self.iter_as_sec = iter_as_sec
                    self.text_iter_as_sec.delete(0, tk.END)
                    self.text_iter_as_sec.insert(tk.END, str(iter_as_sec))
                    if self.is_running:
                        self.after_cancel(self.job_id)
                        self.job_id = self.after(self.interval, threading.Thread(target=self.update_image_array).start())
                except ValueError:
                    pass

            def validate_oil_to_add(self):
                new_value = self.text_oil_added.get()
                try:
                    oil_to_add = float(new_value)
                    self.oil_to_add_on_click = oil_to_add
                    self.text_oil_added.delete(0, tk.END)
                    self.text_oil_added.insert(tk.END, str(oil_to_add))
                except ValueError:
                    pass

            def validate_minimal_oil_to_show(self):
                new_value = self.text_minimal_oil_show.get()
                try:
                    oil_to_show = float(new_value)
                    self.minimal_oil_to_show = oil_to_show
                    self.text_minimal_oil_show.delete(0, tk.END)
                    self.text_minimal_oil_show.insert(tk.END, str(oil_to_show))
                    if self.job_id is not None:
                        self.after_cancel(self.job_id)
                    threading.Thread(target=self.update_image_array).start()
                    self.viewer.update_image()
                except ValueError:
                    pass

            def toggle_start_stop(self):
                if self.is_running:
                    self.stop_image_changes()
                    self.set_oil_spill_on_off.config(state=NORMAL)
                else:
                    self.start_image_changes()
                    self.set_oil_spill_on_off.deselect()
                    self.set_oil_spill_on_off.config(state=DISABLED)
                    self.oil_spill_on_bool = False

            def start_image_changes(self):
                self.is_running = True
                self.btn_start_stop.configure(text="Stop")
                threading.Thread(target=self.update_image_array).start()

            def stop_image_changes(self):
                self.is_running = False
                self.btn_start_stop.configure(text="Start")
                if self.job_id is not None:
                    self.after_cancel(self.job_id)

            def update_image_array(self):
                if engine.is_finished():
                    self.toggle_start_stop()
                    self.options_frame.grid_remove()
                    self.bottom_frame.grid()
                    
                if self.is_running:
                    deleted = engine.update(self.iter_as_sec)
                    for coords in deleted:
                        self.image_array[coords[1]][coords[0]] = rgba_to_rgb(LAND_COLOR) if coords in engine.lands else rgba_to_rgb(SEA_COLOR)
                    self.value_not_yet_processed = 0

                new_oil_mass_sea = 0
                new_oil_mass_land = 0
                for coords, point in engine.world.items():
                    if point.topography == simulation.TopographyState.LAND:
                        var = blend_color(LAND_WITH_OIL_COLOR, LAND_COLOR,
                                          point.oil_mass / self.minimal_oil_to_show,
                                          True)
                        new_oil_mass_land += point.oil_mass
                    else:
                        var = blend_color(OIL_COLOR, SEA_COLOR, point.oil_mass / self.minimal_oil_to_show,
                                          True)
                        new_oil_mass_sea += point.oil_mass
                    self.image_array[coords[1]][coords[0]] = var[:3]

                if self.is_running:
                    self.viewer.update_image()
                    self.curr_iter += 1
                    self.sim_sec_passed += self.iter_as_sec
                    self.job_id = self.after(self.interval, self.update_image_array)

                self.update_infobox()

            def update_infobox(self):
                val1 = str(self.curr_iter)
                val2 = f"{str(self.sim_sec_passed // 3600)}h {str((self.sim_sec_passed // 60) % 60)}m {str(self.sim_sec_passed % 60)}s"
                self.infobox1_values_label.configure(text=val1)
                self.infobox2_values_label.configure(text=val2)

                self.update_oil_amount_infobox()

            def update_oil_amount_infobox(self):
                global_oil_amount_sea, global_oil_amount_land = engine.get_oil_amounts()
                global_oil_amount_sea += self.value_not_yet_processed

                val3 = f"{str(int(global_oil_amount_sea // 10 ** 9))}Mt {str(int(global_oil_amount_sea // 10 ** 6) % 10 ** 3)}kt {str(int(global_oil_amount_sea // 10 ** 3) % 10 ** 3)}t"
                val4 = f"{str(int(global_oil_amount_land // 10 ** 9))}Mt {str(int(global_oil_amount_land // 10 ** 6) % 10 ** 3)}kt {str(int(global_oil_amount_land // 10 ** 3) % 10 ** 3)}t"
                self.infobox3_values_label.configure(text=val3)
                self.infobox4_values_label.configure(text=val4)

            def update_zoom_infobox_value(self):
                val5 = f"{round(self.viewer.zoom_level / self.viewer.initial_zoom_level, 2)} times"
                self.infobox5_values_label.configure(text=val5)

            def oil_spill_on_off(self):
                self.oil_spill_on_bool = not self.oil_spill_on_bool

        # TODO: what if user already data has been processed?
        #  maybe interface for choosing already processed data?
        #  for time saving
        def get_data_processor() -> DataProcessor:
            sym_data_reader = DataReader()
            try:
                path = get_main_path().joinpath("data/test_data")
                sym_data_reader.add_all_from_dir(path)
            except DataValidationException as ex:
                # TODO: some kind of error popup?
                logging.error(f"Data validation exception: {ex}")
                exit(1)

            return sym_data_reader.preprocess(const.SIMULATION_INITIAL_PARAMETERS)

        engine = simulation.SimulationEngine(get_data_processor(), neighborhood)
        image_array = np.array(
            [rgba_to_rgb(LAND_COLOR) if (j, i) in engine.lands else rgba_to_rgb(SEA_COLOR) for i in range(const.POINTS_SIDE_COUNT) for j in
             range(const.POINTS_SIDE_COUNT)]).reshape((const.POINTS_SIDE_COUNT, const.POINTS_SIDE_COUNT, 3)).astype(np.uint8)

        window.rowconfigure(0, weight=5, uniform='row')
        window.rowconfigure(1, weight=1, uniform='row')
        window.columnconfigure(0, weight=2, uniform='column')
        window.columnconfigure(1, weight=1, uniform='column')

        frame_controller = ImageChangeController(window, image_array)

        initial_zoom_level = 1
        viewer = ImageViewer(window, image_array, frame_controller, initial_zoom_level)
        viewer.grid(row=0, column=0, sticky=tk.N + tk.S + tk.E + tk.W)
        frame_controller.set_viewer(viewer)

        frame_controller.update_image_array()
        viewer.update()
        viewer.update_image()

    def start_initial_menu():
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

                self.main_frame = tk.Frame(parent)
                self.main_frame.grid(row=0, column=0, padx=5, pady=5, sticky=tk.N + tk.S + tk.E + tk.W)

                self.main_frame.rowconfigure(0, weight=2, uniform='row')
                self.main_frame.rowconfigure(1, weight=1, uniform='row')
                self.main_frame.rowconfigure(2, weight=1, uniform='row')
                self.main_frame.rowconfigure(3, weight=1, uniform='row')
                self.main_frame.rowconfigure(4, weight=2, uniform='row')
                self.main_frame.rowconfigure(5, weight=2, uniform='row')
                self.main_frame.columnconfigure(0, weight=2, uniform='column')
                self.main_frame.columnconfigure(1, weight=3, uniform='column')
                self.main_frame.columnconfigure(2, weight=1, uniform='column')

                title_frame = tk.Frame(self.main_frame)
                neighborhood_type_frame = tk.Frame(self.main_frame)
                inputs_frame = tk.Frame(self.main_frame)
                data_path_frame = tk.Frame(self.main_frame)
                confirm_and_start_frame = tk.Frame(self.main_frame)

                title_frame.grid(row=0, column=0, rowspan=1, columnspan=3, sticky=tk.N + tk.S)
                neighborhood_type_frame.grid(row=4, column=0, sticky=tk.S + tk.W)
                inputs_frame.grid(row=1, column=0, rowspan=3, columnspan=3, sticky=tk.N + tk.S + tk.W)
                data_path_frame.grid(row=5, column=0, rowspan=1, columnspan=1, sticky=tk.S + tk.W)
                confirm_and_start_frame.grid(row=5, column=2, rowspan=1, columnspan=1, sticky=tk.S + tk.E)

                title_label = tk.Label(title_frame,
                                       text="Oil Spill Simulation",
                                       font=("Arial", 14, "bold"), padx=10, pady=5)
                title_label.pack(side=tk.TOP)

                inputs_frame.rowconfigure(0, weight=1, uniform='row')
                inputs_frame.rowconfigure(1, weight=1, uniform='row')
                inputs_frame.rowconfigure(2, weight=1, uniform='row')
                inputs_frame.columnconfigure(0, weight=5, uniform='column')
                inputs_frame.columnconfigure(1, weight=3, uniform='column')
                inputs_frame.columnconfigure(2, weight=3, uniform='column')
                inputs_frame.columnconfigure(3, weight=3, uniform='column')
                inputs_frame.columnconfigure(4, weight=3, uniform='column')

                top_coord_frame = tk.Frame(inputs_frame)
                down_coord_frame = tk.Frame(inputs_frame)
                left_coord_frame = tk.Frame(inputs_frame)
                right_coord_frame = tk.Frame(inputs_frame)
                time_range_start_frame = tk.Frame(inputs_frame)
                time_range_end_frame = tk.Frame(inputs_frame)
                data_time_step_frame = tk.Frame(inputs_frame)
                cells_side_count_latitude_frame = tk.Frame(inputs_frame)
                cells_side_count_longitude_frame = tk.Frame(inputs_frame)
                point_side_size_frame = tk.Frame(inputs_frame)

                top_coord_frame.grid(row=0, column=1, sticky=tk.N + tk.S)
                down_coord_frame.grid(row=1, column=1, sticky=tk.N + tk.S)
                left_coord_frame.grid(row=0, column=2, sticky=tk.N + tk.S)
                right_coord_frame.grid(row=1, column=2, sticky=tk.N + tk.S)
                time_range_start_frame.grid(row=2, column=1, sticky=tk.N + tk.S)
                time_range_end_frame.grid(row=2, column=2, sticky=tk.N + tk.S)
                data_time_step_frame.grid(row=2, column=3, sticky=tk.N + tk.S)
                cells_side_count_latitude_frame.grid(row=0, column=3, sticky=tk.N + tk.S)
                cells_side_count_longitude_frame.grid(row=1, column=3, sticky=tk.N + tk.S)
                point_side_size_frame.grid(row=1, column=4, sticky=tk.N + tk.S)

                top_coord_label = tk.Label(top_coord_frame,
                                           text="Top coord value\n[latitude]",
                                           font=("Arial", 12, "bold"))
                down_coord_label = tk.Label(down_coord_frame,
                                            text="Bottom coord value\n[latitude]",
                                            font=("Arial", 12, "bold"))
                left_coord_label = tk.Label(left_coord_frame,
                                            text="Left coord value\n[longitude]",
                                            font=("Arial", 12, "bold"))
                right_coord_label = tk.Label(right_coord_frame,
                                             text="Right coord value\n[longitude]",
                                             font=("Arial", 12, "bold"))
                time_range_start_label = tk.Label(time_range_start_frame,
                                                  text="Time range: start\n[yyyy-mm-dd hh:mm:ss]",
                                                  font=("Arial", 12, "bold"))
                time_range_end_label = tk.Label(time_range_end_frame,
                                                text="Time range: end\n[yyyy-mm-dd hh:mm:ss]",
                                                font=("Arial", 12, "bold"))
                data_time_step_label = tk.Label(data_time_step_frame,
                                                text="Data time step\n[min]",
                                                font=("Arial", 12, "bold"))
                cells_side_count_latitude_label = tk.Label(cells_side_count_latitude_frame,
                                                           text="Data stations count:\nlatitude",
                                                           font=("Arial", 12, "bold"))
                cells_side_count_longitude_label = tk.Label(cells_side_count_longitude_frame,
                                                            text="Data stations count:\nlongitude",
                                                            font=("Arial", 12, "bold"))
                point_side_size_label = tk.Label(point_side_size_frame,
                                                            text="Point side size\n[m]",
                                                            font=("Arial", 12, "bold"))

                top_coord_label.grid(row=0, column=0, padx=3, pady=3, sticky=tk.N + tk.S)
                down_coord_label.grid(row=0, column=0, padx=3, pady=3, sticky=tk.N + tk.S)
                left_coord_label.grid(row=0, column=0, padx=3, pady=3, sticky=tk.N + tk.S)
                right_coord_label.grid(row=0, column=0, padx=3, pady=3, sticky=tk.N + tk.S)
                time_range_start_label.grid(row=0, column=0, padx=3, pady=3, sticky=tk.N + tk.S)
                time_range_end_label.grid(row=0, column=0, padx=3, pady=3, sticky=tk.N + tk.S)
                data_time_step_label.grid(row=0, column=0, padx=3, pady=3, sticky=tk.N + tk.S)
                cells_side_count_latitude_label.grid(row=0, column=0, padx=3, pady=3, sticky=tk.N + tk.S)
                cells_side_count_longitude_label.grid(row=0, column=0, padx=3, pady=3, sticky=tk.N + tk.S)
                point_side_size_label.grid(row=0, column=0, padx=3, pady=3, sticky=tk.N + tk.S)

                self.top_coord_input = tk.Entry(top_coord_frame, width=9)
                self.top_coord_input.insert(tk.END, str(self.top_coord))
                self.top_coord_input.bind("<KeyPress>", self.on_key_press_validate_coordinates_top)
                self.top_coord_input.bind("<FocusOut>", self.on_focus_out_validate_coordinates_top)

                self.down_coord_input = tk.Entry(down_coord_frame, width=9)
                self.down_coord_input.insert(tk.END, str(self.down_coord))
                self.down_coord_input.bind("<KeyPress>", self.on_key_press_validate_coordinates_down)
                self.down_coord_input.bind("<FocusOut>", self.on_focus_out_validate_coordinates_down)

                self.left_coord_input = tk.Entry(left_coord_frame, width=9)
                self.left_coord_input.insert(tk.END, str(self.left_coord))
                self.left_coord_input.bind("<KeyPress>", self.on_key_press_validate_coordinates_left)
                self.left_coord_input.bind("<FocusOut>", self.on_focus_out_validate_coordinates_left)

                self.right_coord_input = tk.Entry(right_coord_frame, width=9)
                self.right_coord_input.insert(tk.END, str(self.right_coord))
                self.right_coord_input.bind("<KeyPress>", self.on_key_press_validate_coordinates_right)
                self.right_coord_input.bind("<FocusOut>", self.on_focus_out_validate_coordinates_right)

                self.time_range_start_input = tk.Entry(time_range_start_frame, width=17)
                self.time_range_start_input.insert(tk.END, str(self.time_range_start))
                self.time_range_start_input.bind("<KeyPress>", self.on_key_press_validate_time_range_start)
                self.time_range_start_input.bind("<FocusOut>", self.on_focus_out_validate_time_range_start)

                self.time_range_end_input = tk.Entry(time_range_end_frame, width=17)
                self.time_range_end_input.insert(tk.END, str(self.time_range_end))
                self.time_range_end_input.bind("<KeyPress>", self.on_key_press_validate_time_range_end)
                self.time_range_end_input.bind("<FocusOut>", self.on_focus_out_validate_time_range_end)

                self.data_time_step_input = tk.Entry(data_time_step_frame, width=3)
                self.data_time_step_input.insert(tk.END, str(self.data_time_step_minutes))
                self.data_time_step_input.bind("<KeyPress>", self.on_key_press_validate_data_time_step)
                self.data_time_step_input.bind("<FocusOut>", self.on_focus_out_validate_data_time_step)

                self.cells_side_count_latitude_input = tk.Entry(cells_side_count_latitude_frame, width=3)
                self.cells_side_count_latitude_input.insert(tk.END, str(self.cells_side_count_latitude))
                self.cells_side_count_latitude_input.bind("<KeyPress>", self.on_key_press_validate_cells_side_count_latitude)
                self.cells_side_count_latitude_input.bind("<FocusOut>", self.on_focus_out_validate_cells_side_count_latitude)

                self.cells_side_count_longitude_input = tk.Entry(cells_side_count_longitude_frame, width=3)
                self.cells_side_count_longitude_input.insert(tk.END, str(self.cells_side_count_longitude))
                self.cells_side_count_longitude_input.bind("<KeyPress>", self.on_key_press_validate_cells_side_count_longitude)
                self.cells_side_count_longitude_input.bind("<FocusOut>", self.on_focus_out_validate_cells_side_count_longitude)

                self.point_side_size_input = tk.Entry(point_side_size_frame, width=3)
                self.point_side_size_input.insert(tk.END, str(self.point_side_size))
                self.point_side_size_input.bind("<KeyPress>", self.on_key_press_validate_point_side_size)
                self.point_side_size_input.bind("<FocusOut>", self.on_focus_out_validate_point_side_size)

                self.top_coord_input.grid(row=1, column=0, padx=3, pady=3, sticky=tk.N + tk.S)
                self.down_coord_input.grid(row=1, column=0, padx=3, pady=3, sticky=tk.N + tk.S)
                self.left_coord_input.grid(row=1, column=0, padx=3, pady=3, sticky=tk.N + tk.S)
                self.right_coord_input.grid(row=1, column=0, padx=3, pady=3, sticky=tk.N + tk.S)
                self.time_range_start_input.grid(row=1, column=0, padx=3, pady=3, sticky=tk.N + tk.S)
                self.time_range_end_input.grid(row=1, column=0, padx=3, pady=3, sticky=tk.N + tk.S)
                self.data_time_step_input.grid(row=1, column=0, padx=3, pady=3, sticky=tk.N + tk.S)
                self.cells_side_count_latitude_input.grid(row=1, column=0, padx=3, pady=3, sticky=tk.N + tk.S)
                self.cells_side_count_longitude_input.grid(row=1, column=0, padx=3, pady=3, sticky=tk.N + tk.S)
                self.point_side_size_input.grid(row=1, column=0, padx=3, pady=3, sticky=tk.N + tk.S)

                self.top_coord_validation_label = tk.Label(top_coord_frame,
                                                           text="Default value",
                                                           font=("Arial", 8, "bold"), padx=3, pady=3)
                self.down_coord_validation_label = tk.Label(down_coord_frame,
                                                            text="Default value",
                                                            font=("Arial", 8, "bold"), padx=3, pady=3)
                self.left_coord_validation_label = tk.Label(left_coord_frame,
                                                            text="Default value",
                                                            font=("Arial", 8, "bold"), padx=3, pady=3)
                self.right_coord_validation_label = tk.Label(right_coord_frame,
                                                             text="Default value",
                                                             font=("Arial", 8, "bold"), padx=3, pady=3)
                self.time_range_start_validation_label = tk.Label(time_range_start_frame,
                                                                  text="Default value",
                                                                  font=("Arial", 8, "bold"), padx=3, pady=3)
                self.time_range_end_validation_label = tk.Label(time_range_end_frame,
                                                                text="Default value",
                                                                font=("Arial", 8, "bold"), padx=3, pady=3)
                self.data_time_step_validation_label = tk.Label(data_time_step_frame,
                                                                text="Default value",
                                                                font=("Arial", 8, "bold"), padx=3, pady=3)
                self.cells_side_count_latitude_validation_label = tk.Label(cells_side_count_latitude_frame,
                                                                           text="Default value",
                                                                           font=("Arial", 8, "bold"), padx=3, pady=3)
                self.cells_side_count_longitude_validation_label = tk.Label(cells_side_count_longitude_frame,
                                                                            text="Default value",
                                                                            font=("Arial", 8, "bold"), padx=3, pady=3)
                self.point_side_size_validation_label = tk.Label(point_side_size_frame,
                                                                            text="Default value",
                                                                            font=("Arial", 8, "bold"), padx=3, pady=3)

                self.top_coord_validation_label.grid(row=2, column=0, padx=3, pady=3, sticky=tk.N + tk.S)
                self.down_coord_validation_label.grid(row=2, column=0, padx=3, pady=3, sticky=tk.N + tk.S)
                self.left_coord_validation_label.grid(row=2, column=0, padx=3, pady=3, sticky=tk.N + tk.S)
                self.right_coord_validation_label.grid(row=2, column=0, padx=3, pady=3, sticky=tk.N + tk.S)
                self.time_range_start_validation_label.grid(row=2, column=0, padx=3, pady=3, sticky=tk.N + tk.S)
                self.time_range_end_validation_label.grid(row=2, column=0, padx=3, pady=3, sticky=tk.N + tk.S)
                self.data_time_step_validation_label.grid(row=2, column=0, padx=3, pady=3, sticky=tk.N + tk.S)
                self.cells_side_count_latitude_validation_label.grid(row=2, column=0, padx=3, pady=3, sticky=tk.N + tk.S)
                self.cells_side_count_longitude_validation_label.grid(row=2, column=0, padx=3, pady=3, sticky=tk.N + tk.S)
                self.point_side_size_validation_label.grid(row=2, column=0, padx=3, pady=3, sticky=tk.N + tk.S)

                self.loaded_img = Image.open(os.path.join(get_main_path(), "data/Blue_Marble_2002.png"))

                self.map_view_frame = tk.Frame(inputs_frame)
                self.map_view_frame.grid(row=0, column=0, rowspan=4, padx=3, pady=3, sticky=tk.N + tk.S)

                self.map_view = tk.Canvas(self.map_view_frame)
                self.load_and_crop_image()

                self.map_view.grid(row=0, column=0, rowspan=3, padx=3, pady=3, sticky=tk.N + tk.S)

                # self.manual_map_coords_selection = tk.Button(self.map_view_frame, text='manual_coords_selection TODO',
                #                                              command=self.manual_map_coords_selection)
                # self.manual_map_coords_selection.grid(row=4, column=0, padx=3, pady=3, sticky=tk.N + tk.S)

                neighborhood_label = tk.Label(neighborhood_type_frame,
                                              text="Neighborhood type:",
                                              font=("Arial", 14, "bold"), padx=3, pady=3)
                neighborhood_label.grid(row=0, column=0, rowspan=1, padx=3, pady=3, sticky=tk.N + tk.S)

                self.neighborhood_var = tk.IntVar()
                NM = tk.Radiobutton(neighborhood_type_frame, text="Moore", variable=self.neighborhood_var, value=0)
                NVN = tk.Radiobutton(neighborhood_type_frame, text="Von Neumann", variable=self.neighborhood_var, value=1)
                NM.select()

                NM.grid(row=1, column=0, rowspan=1, padx=3, pady=3, sticky=tk.N + tk.S)
                NVN.grid(row=2, column=0, rowspan=1, padx=3, pady=3, sticky=tk.N + tk.S)

                self.data_path = tk.StringVar()
                self.data_path.set(get_data_path())
                path_label = tk.Label(data_path_frame,
                                      text="Data files path:",
                                      font=("Arial", 14, "bold"), padx=10, pady=5)
                path_label.grid(row=0, column=0, columnspan=2, padx=3, pady=3, sticky=tk.N + tk.S + tk.W)

                browse_path_label = tk.Label(data_path_frame, textvariable=self.data_path)
                browse_path_label.grid(row=1, column=1, padx=3, pady=3, sticky=tk.N + tk.S + tk.W)

                data_path_browse = tk.Button(data_path_frame, text="Browse", command=self.browse_button)
                data_path_browse.grid(row=1, column=0, padx=3, pady=3, sticky=tk.N + tk.S + tk.W)

                self.confirm_and_continue = tk.Button(confirm_and_start_frame, text='Confirm and continue',
                                                      command=self.confirm_and_start_simulation)
                self.confirm_and_continue.pack(side=tk.RIGHT, padx=5, pady=5)

                self.validate_all_parameters()

            def on_key_press_validate_coordinates_top(self, event):
                if event.keysym == "Return":
                    self.validate_coordinates_top()

            def on_focus_out_validate_coordinates_top(self, _):
                self.validate_coordinates_top()

            def on_key_press_validate_coordinates_down(self, event):
                if event.keysym == "Return":
                    self.validate_coordinates_down()

            def on_focus_out_validate_coordinates_down(self, _):
                self.validate_coordinates_down()

            def on_key_press_validate_coordinates_left(self, event):
                if event.keysym == "Return":
                    self.validate_coordinates_left()

            def on_focus_out_validate_coordinates_left(self, _):
                self.validate_coordinates_left()

            def on_key_press_validate_coordinates_right(self, event):
                if event.keysym == "Return":
                    self.validate_coordinates_right()

            def on_focus_out_validate_coordinates_right(self, _):
                self.validate_coordinates_right()

            def on_key_press_validate_time_range_start(self, event):
                if event.keysym == "Return":
                    self.validate_time_range_start()

            def on_focus_out_validate_time_range_start(self, _):
                self.validate_time_range_start()

            def on_key_press_validate_time_range_end(self, event):
                if event.keysym == "Return":
                    self.validate_time_range_end()

            def on_focus_out_validate_time_range_end(self, _):
                self.validate_time_range_end()

            def on_key_press_validate_data_time_step(self, event):
                if event.keysym == "Return":
                    self.validate_data_time_step()

            def on_focus_out_validate_data_time_step(self, _):
                self.validate_data_time_step()

            def on_key_press_validate_cells_side_count_latitude(self, event):
                if event.keysym == "Return":
                    self.validate_cells_side_count_latitude()

            def on_focus_out_validate_cells_side_count_latitude(self, _):
                self.validate_cells_side_count_latitude()

            def on_key_press_validate_cells_side_count_longitude(self, event):
                if event.keysym == "Return":
                    self.validate_cells_side_count_longitude()

            def on_focus_out_validate_cells_side_count_longitude(self, _):
                self.validate_cells_side_count_longitude()

            def on_focus_out_validate_point_side_size(self, event):
                if event.keysym == "Return":
                    self.validate_point_side_size()

            def on_key_press_validate_point_side_size(self, _):
                self.validate_point_side_size()

            def validate_coordinates_top(self, is_first_run=True):
                value = self.top_coord_input.get()
                if value:
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
                return False

            def validate_coordinates_down(self, is_first_run=True):
                value = self.down_coord_input.get()
                if value:
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
                return False

            def validate_coordinates_left(self, is_first_run=True):
                value = self.left_coord_input.get()
                if value:
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
                return False

            def validate_coordinates_right(self, is_first_run=True):
                value = self.right_coord_input.get()
                if value:
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
                return False

            def validate_time_range_start(self):
                value = self.time_range_start_input.get()
                if value:
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
                return False

            def validate_time_range_end(self):
                value = self.time_range_end_input.get()
                if value:
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
                return False

            def validate_data_time_step(self):
                value = self.data_time_step_input.get()
                if value:
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
                return False

            def validate_cells_side_count_latitude(self):
                value = self.cells_side_count_latitude_input.get()
                if value:
                    try:
                        if float(value) % 1 == 0 and float(value) > 0:  # TODO I don't really know how to validate this value
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
                return False

            def validate_cells_side_count_longitude(self):
                value = self.cells_side_count_longitude_input.get()
                if value:
                    try:
                        if float(value) % 1 == 0 and float(value) > 0:  # TODO I don't really know how to validate this value
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
                return False

            def validate_point_side_size(self):
                value = self.point_side_size_input.get()
                if value:
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
                return False

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

                start_simulation(Neighbourhood.MOORE if self.neighborhood_var.get() == 0 else Neighbourhood.VON_NEUMANN)

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

                cropped_img = self.loaded_img.crop((longitude_west_bound, latitude_upper_bound, longitude_east_bound, latitude_lower_bound))

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

    default_window_width = 1280
    default_window_height = 720

    window = tk.Tk()
    window.geometry(f"{default_window_width}x{default_window_height}")
    window.title('Oil Spill Simulation')
    window.rowconfigure(0, weight=1, uniform='row')
    window.columnconfigure(0, weight=1, uniform='column')

    start_initial_menu()

    window.mainloop()
