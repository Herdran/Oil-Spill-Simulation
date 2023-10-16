import os
import tkinter as tk
from pathlib import Path
from tkinter import DISABLED, NORMAL

import numpy as np
import threading
from PIL import Image, ImageTk

import simulation.simulation as simulation
from simulation.utilities import Neighbourhood
from color import rgba, blend_color
from constatnts import ITER_AS_SEC, POINTS_SIDE_COUNT, SIMULATION_INITIAL_PARAMETERS
from data.data_processor import DataProcessor, DataReader, DataValidationException
from data.utilities import kelvins_to_celsius
from color import rgba, blend_color

def get_tooltip_text(point: simulation.Point) -> str:
    return f"""Oil mass: {point.oil_mass: .2f}kg
--------------------
Wind speed N: {point.wind_velocity[0]: .2f}m/s
Wind speed E: {point.wind_velocity[1]: .2f}m/s
Current speed N: {point.wave_velocity[0]: .2f}m/s
Current speed E: {point.wave_velocity[1]: .2f}m/s
Temperature: {kelvins_to_celsius(point.temperature): .2f}°C"""


def run():
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
            # self.preview_mode = True
            self.preview_mode = False

            self.bind("<MouseWheel>", self.on_mousewheel)
            self.bind("<ButtonPress-1>", self.on_button_press)
            self.bind("<B1-Motion>", self.on_button_motion)
            self.bind("<ButtonRelease-1>", self.on_button_release)
            self.bind("<Motion>", self.on_motion)
            self.bind("<Leave>", self.on_leave)

        def update_image(self):
            self.zoomed_width = int(self.image_array_width * self.zoom_level)
            self.zoomed_height = int(self.image_array_height * self.zoom_level)

            window_width = frame_viewer.winfo_width()
            window_height = frame_viewer.winfo_height()

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

            window_width = frame_viewer.winfo_width()
            window_height = frame_viewer.winfo_height()

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
            x = int((event.x - self.pan_x) / self.zoom_level)
            y = int((event.y - self.pan_y) / self.zoom_level)
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

        def resize(self):
            window_width = frame_viewer.winfo_width()
            window_height = frame_viewer.winfo_height()
            self.zoom_level /= self.initial_zoom_level
            self.initial_zoom_level = min(window_width / image_array.shape[1], window_height / image_array.shape[0])
            self.zoom_level *= self.initial_zoom_level
            self.update_image()

        def define_simulation_area(self):
            print(self.pan_x, self.pan_y)
            print(self.zoom_level)

            self.preview_mode = False
            height, width, channels = self.image_array.shape
            self.zoomed_width = int(width * self.zoom_level)
            self.zoomed_height = int(height * self.zoom_level)

            window_width = frame_viewer.winfo_width()
            window_height = frame_viewer.winfo_height()

            self.pan_x = max(min(self.pan_x, 0), min(window_width - self.zoomed_width, 0))
            self.pan_y = max(min(self.pan_y, 0), min(window_height - self.zoomed_height, 0))

            self.image_array = self.image_array[
                               int(-self.pan_y / self.zoom_level):
                               int(window_height / self.zoom_level - (self.pan_y / self.zoom_level)),
                               int(-self.pan_x / self.zoom_level):
                               int(window_width / self.zoom_level - (self.pan_x / self.zoom_level))
                               ]
            self.prev_x = 0
            self.prev_y = 0
            self.pan_x = 0
            self.pan_y = 0
            self.initial_zoom_level = self.zoom_level

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
            self.interval = 1
            self.job_id = None
            self.is_updating = False
            self.curr_iter = 0
            self.sim_sec_passed = 0
            self.oil_to_add_on_click = 10000
            self.minimal_oil_to_show = 100
            self.iter_as_sec = ITER_AS_SEC
            self.viewer = None
            self.value_not_yet_processed = 0
            self.oil_spill_on_bool = True

            self.options_frame = tk.Frame(window)
            self.options_frame.grid(row=1, column=0, rowspan=1, padx=10, pady=10, sticky=tk.N + tk.S + tk.E)
            start_stop_frame = tk.Frame(self.options_frame)
            interval_frame = tk.Frame(self.options_frame)
            iter_as_sec_frame = tk.Frame(self.options_frame)
            oil_added_frame = tk.Frame(self.options_frame)
            minimal_oil_value_to_show_frame = tk.Frame(self.options_frame)

            start_stop_frame.grid(row=1, column=0, rowspan=1, padx=10, pady=10, sticky=tk.N + tk.S)
            interval_frame.grid(row=1, column=1, rowspan=1, padx=10, pady=10, sticky=tk.N + tk.S)
            iter_as_sec_frame.grid(row=1, column=2, rowspan=1, padx=10, pady=10, sticky=tk.N + tk.S)
            oil_added_frame.grid(row=1, column=3, rowspan=1, padx=10, pady=10, sticky=tk.N + tk.S)
            minimal_oil_value_to_show_frame.grid(row=1, column=4, rowspan=1, padx=10, pady=10, sticky=tk.N + tk.S)

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

            self.confirm_size = tk.Frame(window)
            self.confirm_size.grid(row=1, column=0, rowspan=1, padx=10, pady=10, sticky=tk.N + tk.S + tk.E)
            confirm_frame = tk.Frame(self.confirm_size)

            confirm_frame.grid(row=1, column=0, rowspan=1, padx=10, pady=10, sticky=tk.N + tk.S)

            self.confirm_btn = tk.Button(confirm_frame, text="Confirm", width=10, command=self.confirm_func)
            self.confirm_btn.pack(side=tk.TOP, padx=5, pady=5)

            self.infoboxes_frame = tk.Frame(window)
            self.infoboxes_frame.grid(row=0, column=1, rowspan=1, padx=10, pady=10, sticky=tk.N + tk.S + tk.E)
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

            self.update_image_array()
            self.update_infobox()

            self.bind("<Configure>", self.resize)
            # self.options_frame.grid_remove()
            # self.infoboxes_frame.grid_remove()
            self.confirm_size.grid_remove()

        def set_viewer(self, viewer):
            self.viewer = viewer

        def resize(self, event):
            if self.viewer:
                self.viewer.resize()

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
                interval = max(0.1, min(2.0, interval))
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

        def confirm_func(self):
            self.confirm_size.grid_remove()
            self.options_frame.grid()
            self.infoboxes_frame.grid()
            frame_viewer.update()
            self.viewer.define_simulation_area()

        def update_image_array(self):
            if self.is_running:
                deleted = engine.update(self.iter_as_sec)
                for coords in deleted:
                    land_color = (38, 166, 91)
                    ocean_color = (15, 10, 222)
                    self.image_array[coords[1]][coords[0]] = land_color if coords in engine.lands else ocean_color
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
                self.job_id = self.after(self.interval, threading.Thread(target=self.update_image_array).start())

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
            path = Path("data/test_data")
            if os.getcwd().endswith('src'):
                path = os.path.join('..', path)
            sym_data_reader.add_all_from_dir(path)
        except DataValidationException as ex:
            # TODO: some kind of error popup?
            print("Error with Data Validation: ", ex)
            exit(1)

        return sym_data_reader.preprocess(SIMULATION_INITIAL_PARAMETERS)

    #TODO choose neighborhood type in gui
    neighborhood = Neighbourhood.MOORE
    engine = simulation.SimulationEngine(get_data_processor(), neighborhood)
    land_color = (38, 166, 91)
    ocean_color = (15, 10, 222)
    image_array = np.array(
        [land_color if (j, i) in engine.lands else ocean_color for i in range(POINTS_SIDE_COUNT) for j in
         range(POINTS_SIDE_COUNT)]).reshape((POINTS_SIDE_COUNT, POINTS_SIDE_COUNT, 3)).astype(np.uint8)

    default_window_width = 1280
    default_window_height = 720

    window = tk.Tk()
    window.geometry(f"{default_window_width}x{default_window_height}")
    window.title('Oil Spill Simulation')

    frame_viewer = tk.Frame(window)
    frame_viewer.grid(row=0, column=0, rowspan=10, padx=10, pady=10, sticky=tk.N + tk.S + tk.E + tk.W)

    frame_controller = ImageChangeController(window, image_array)
    frame_controller.grid(row=1, column=0, padx=10, pady=10, sticky=tk.N + tk.S + tk.E + tk.W)

    window.grid_rowconfigure(0, weight=1)
    window.grid_columnconfigure(0, weight=1)
    frame_viewer.grid_rowconfigure(0, weight=1)
    frame_viewer.grid_columnconfigure(0, weight=1)

    frame_viewer.update()
    window_width = frame_viewer.winfo_width()
    window_height = frame_viewer.winfo_height()

    initial_zoom_level = min(window_width / image_array.shape[1], window_height / image_array.shape[0])
    viewer = ImageViewer(frame_viewer, image_array, frame_controller, initial_zoom_level)
    viewer.grid(row=0, column=0, rowspan=10, sticky=tk.N + tk.S + tk.E + tk.W)
    frame_controller.set_viewer(viewer)

    frame_controller.update_image_array()
    viewer.update()
    viewer.update_image()

    window.mainloop()
