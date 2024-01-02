import logging
import threading
import tkinter as tk
from copy import deepcopy
from tkinter import DISABLED, NORMAL

import numpy as np
from PIL import Image, ImageTk

import simulation.simulation as simulation
from checkpoints import initialize_points_from_checkpoint
from color import blend_color
from data.data_processor import DataProcessor, DataReader, DataValidationException
from gui.utilities import get_tooltip_text, create_frame, create_label_pack, create_input_entry_pack, \
    generate_string_for_displaying_oil_amount, stop_thread_on_closing, generate_string_for_displaying_time, \
    create_label_grid
from initial_values import InitialValues

Image.MAX_IMAGE_PIXELS = 999999999999


def start_simulation(window, points=None, oil_sources=None):
    class ImageViewer(tk.Canvas):
        def __init__(self, parent, image_array_shape, image_change_controller, initial_zoom_level, full_img):
            super().__init__(parent)
            self.image_array_height, self.image_array_width, _ = image_array_shape
            self.initial_zoom_level = initial_zoom_level
            self.zoom_level = initial_zoom_level
            self.zoomed_width = int(self.image_array_width * initial_zoom_level)
            self.zoomed_height = int(self.image_array_height * initial_zoom_level)
            self.image_id = None
            self.prev_x = 0
            self.prev_y = 0
            self.pan_x = 0
            self.pan_y = 0
            self.is_holding = None
            self.is_panning = None
            self.tooltip = None
            self.full_img = full_img
            self.current_img = None
            self.image_change_controller = image_change_controller
            self.tooltip_coord = None

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

            left = int(-self.pan_x / self.zoom_level)
            top = int(-self.pan_y / self.zoom_level)
            right = int(window_width / self.zoom_level - (self.pan_x / self.zoom_level))
            bottom = int(window_height / self.zoom_level - (self.pan_y / self.zoom_level))

            right = min(right, self.image_array_width)
            bottom = min(bottom, self.image_array_height)

            cropped_image = self.full_img.crop((left, top, right, bottom))

            self.current_img = cropped_image.resize((min(window_width, self.zoomed_width),
                                                     min(window_height, self.zoomed_height)),
                                                    Image.NEAREST)

            self.current_img = ImageTk.PhotoImage(self.current_img)

            self.image_id = self.create_image(max(0, (window_width - self.zoomed_width) // 2),
                                              max(0, (window_height - self.zoomed_height) // 2),
                                              anchor=tk.NW,
                                              image=self.current_img)

        def on_mousewheel(self, event):
            zoom_factor = 1.1 if event.delta > 0 else 10 / 11

            window_width = self.winfo_width()
            window_height = self.winfo_height()

            x = int((event.x - self.pan_x - max((window_width - self.zoomed_width) // 2, 0)) / self.zoom_level)
            y = int((event.y - self.pan_y - max((window_height - self.zoomed_height) // 2, 0)) / self.zoom_level)

            self.pan_x /= self.zoom_level
            self.pan_y /= self.zoom_level

            self.zoom_level *= zoom_factor
            self.zoom_level = min(max(self.zoom_level, self.initial_zoom_level), 100)

            self.pan_x *= self.zoom_level
            self.pan_y *= self.zoom_level

            self.zoomed_width = int(self.image_array_width * self.zoom_level)
            self.zoomed_height = int(self.image_array_height * self.zoom_level)

            new_x = int((event.x - self.pan_x - max((window_width - self.zoomed_width) // 2, 0)) / self.zoom_level)
            new_y = int((event.y - self.pan_y - max((window_height - self.zoomed_height) // 2, 0)) / self.zoom_level)

            self.pan_x += new_x - x
            self.pan_y += new_y - y

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
                return
            if not self.image_change_controller.oil_spill_on_bool:
                return
            window_width = self.winfo_width()
            window_height = self.winfo_height()
            x = int((event.x - self.pan_x - max((window_width - self.zoomed_width) // 2, 0)) / self.zoom_level)
            y = int((event.y - self.pan_y - max((window_height - self.zoomed_height) // 2, 0)) / self.zoom_level)
            if 0 <= x < self.image_array_width and 0 <= y < self.image_array_height:
                coord = (x, y)
                if simulation_engine.get_topography(coord) == simulation.TopographyState.SEA:
                    if coord not in simulation_engine.world:
                        simulation_engine.world[coord] = simulation.Point(coord, simulation_engine)

                    point_clicked = simulation_engine.world[coord]
                    point_clicked.add_oil(self.image_change_controller.oil_to_add_on_click)

                    var = blend_color(InitialValues.OIL_COLOR, InitialValues.SEA_COLOR,
                                      point_clicked.oil_mass / self.image_change_controller.minimal_oil_to_show)
                    self.image_change_controller.update_infobox()
                    self.full_img.putpixel((x, y), var)
                    self.update_image()
                    self.tooltip_coord = coord
                    self.show_tooltip(event.x_root, event.y_root)
                    self.image_change_controller.value_not_yet_processed += self.image_change_controller.oil_to_add_on_click
            self.image_change_controller.update_oil_amount_infobox()

        def on_button_motion(self, event):
            if not self.is_holding:
                return
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
            self.tooltip_coord = (x, y)

            if not (0 <= self.tooltip_coord[0] < self.image_array_width and 0 <= self.tooltip_coord[1] < self.image_array_height):
                self.hide_tooltip()
                return
            self.show_tooltip(event.x_root, event.y_root)

        def on_leave(self, _):
            self.hide_tooltip()

        def show_tooltip(self, x, y):
            if self.tooltip is None:
                self.tooltip = ToolTip(self, x, y, "")
            else:
                self.tooltip.update_position(x, y)
            self.update_tooltip_text()

        def update_tooltip_text(self):
            if self.tooltip:
                if self.tooltip_coord not in simulation_engine.world:
                    text = f"Oil mass: {0: .2f}kg"
                else:
                    tooltip_point = simulation_engine.world[self.tooltip_coord]
                    text = get_tooltip_text(tooltip_point)
                self.tooltip.update_text(text)

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
        def __init__(self, parent, full_img):
            super().__init__(parent)
            self.is_running = False
            self.interval = 100
            self.job_id = None
            self.is_updating = False
            self.curr_iter = InitialValues.curr_iter
            self.oil_to_add_on_click = 10000
            self.minimal_oil_to_show = InitialValues.minimal_oil_to_show
            self.iter_as_sec = InitialValues.iter_as_sec
            self.viewer = None
            self.value_not_yet_processed = 0
            self.oil_spill_on_bool = True
            self.full_img = full_img
            self.update_occurred = False
            self.thread_finished = False
            self.event_wait_for_gui_update = threading.Event()

            self.options_frame = create_frame(parent, 1, 0, 1, 2, tk.N + tk.S, 3, 3, relief_style=tk.RAISED)
            self.options_frame.columnconfigure(0, weight=2)
            self.options_frame.columnconfigure(1, weight=2)
            self.options_frame.columnconfigure(2, weight=2)
            self.options_frame.columnconfigure(3, weight=2)
            self.options_frame.columnconfigure(4, weight=1)
            self.options_frame.columnconfigure(5, weight=1)

            interval_frame = create_frame(self.options_frame, 0, 0, 1, 1, tk.N + tk.S, 3, 3)
            oil_added_frame = create_frame(self.options_frame, 0, 1, 1, 1, tk.N + tk.S, 3, 3)
            minimal_oil_value_to_show_frame = create_frame(self.options_frame, 0, 2, 1, 1, tk.N + tk.S, 3, 3)
            buttons_frame = create_frame(self.options_frame, 0, 3, 1, 2, tk.N + tk.S + tk.E, 3, 3)

            create_label_pack(interval_frame, "Interval of changes [s]")
            create_label_pack(oil_added_frame, "Oil added on click [kg]")

            self.oil_spill_on_var = tk.IntVar()
            self.set_oil_spill_on_off = tk.Checkbutton(oil_added_frame,
                                                       text="ON/OFF",
                                                       variable=self.oil_spill_on_var,
                                                       onvalue=1,
                                                       offvalue=0,
                                                       command=self.oil_spill_on_off)
            self.set_oil_spill_on_off.pack(side=tk.TOP)
            self.set_oil_spill_on_off.select()

            create_label_pack(minimal_oil_value_to_show_frame, "Minimal oil value to show [kg]")

            self.btn_start_stop = tk.Button(buttons_frame, text="Start", width=15, command=self.toggle_start_stop)
            self.btn_start_stop.pack(side=tk.TOP, padx=5, pady=5)

            self.btn_save_checkpoint = tk.Button(buttons_frame, text="Save checkpoint", width=15,
                                                 command=self.save_checkpoint)
            self.btn_save_checkpoint.pack(side=tk.TOP, padx=5, pady=5)

            self.text_interval = create_input_entry_pack(interval_frame, 10, str(self.interval / 1000),
                                                         self.validate_interval)
            self.text_oil_added = create_input_entry_pack(oil_added_frame, 10, str(self.oil_to_add_on_click),
                                                          self.validate_oil_to_add)
            self.text_minimal_oil_show = create_input_entry_pack(minimal_oil_value_to_show_frame, 10,
                                                                 str(self.minimal_oil_to_show),
                                                                 self.validate_minimal_oil_to_show)

            self.infoboxes_frame = create_frame(parent, 0, 1, 1, 1, tk.N + tk.S, 3, 3)

            self.infoboxes_frame.columnconfigure(0, weight=1, uniform='column')
            self.infoboxes_frame.columnconfigure(1, weight=1, uniform='column')

            frame_infoboxes_labels = create_frame(self.infoboxes_frame, 0, 0, 1, 1, tk.N + tk.S + tk.E, 5, 5)

            create_label_grid(frame_infoboxes_labels, "Current iteration", 0, 0, sticky=tk.N + tk.S + tk.W)
            create_label_grid(frame_infoboxes_labels, "Simulation time", 1, 0, sticky=tk.N + tk.S + tk.W)
            create_label_grid(frame_infoboxes_labels, "Global oil amount [sea]", 2, 0, sticky=tk.N + tk.S + tk.W)
            create_label_grid(frame_infoboxes_labels, "Global oil amount [land]", 3, 0, sticky=tk.N + tk.S + tk.W)
            create_label_grid(frame_infoboxes_labels, "Dispersed oil", 4, 0, sticky=tk.N + tk.S + tk.W)
            create_label_grid(frame_infoboxes_labels, "Evaporated oil", 5, 0, sticky=tk.N + tk.S + tk.W)
            create_label_grid(frame_infoboxes_labels, "Oil area", 6, 0, sticky=tk.N + tk.S + tk.W)
            create_label_grid(frame_infoboxes_labels, "Current zoom", 7, 0, sticky=tk.N + tk.S + tk.W)

            frame_infoboxes_values = create_frame(self.infoboxes_frame, 0, 1, 1, 1, tk.N + tk.S + tk.E, 5, 5)

            self.infobox_current_iteration = create_label_grid(frame_infoboxes_values, "", 0, 0, sticky=tk.N + tk.S + tk.E, anchor="e", justify="right")
            self.infobox_simulation_time = create_label_grid(frame_infoboxes_values, "", 1, 0, sticky=tk.N + tk.S + tk.E, anchor="e", justify="right")
            self.infobox_global_oil_amount_sea = create_label_grid(frame_infoboxes_values, "", 2, 0, sticky=tk.N + tk.S + tk.E, anchor="e", justify="right")
            self.infobox_global_oil_amount_land = create_label_grid(frame_infoboxes_values, "", 3, 0, sticky=tk.N + tk.S + tk.E, anchor="e", justify="right")
            self.infobox_dispersed_oil = create_label_grid(frame_infoboxes_values, "", 4, 0, sticky=tk.N + tk.S + tk.E, anchor="e", justify="right")
            self.infobox_evaporated_oil = create_label_grid(frame_infoboxes_values, "", 5, 0, sticky=tk.N + tk.S + tk.E, anchor="e", justify="right")
            self.infobox_oil_area = create_label_grid(frame_infoboxes_values, "", 6, 0, sticky=tk.N + tk.S + tk.E, anchor="e", justify="right")
            self.infobox_current_zoom = create_label_grid(frame_infoboxes_values, "1.0", 7, 0, sticky=tk.N + tk.S + tk.E, anchor="e", justify="right")

            self.bottom_frame = create_frame(parent, 1, 0, 1, 2, tk.N + tk.S, 3, 3, relief_style=tk.RAISED)

            create_label_grid(self.bottom_frame, "Simulation finished!")
            self.bottom_frame.grid_remove()

            self.update_infobox()

        def set_viewer(self, viewer):
            self.viewer = viewer
            self.update_image_array(True)

        def validate_interval(self):
            new_value = self.text_interval.get()
            try:
                interval = float(new_value)
                interval = max(0.01, min(2.0, interval))
                self.interval = int(interval * 1000)
                self.text_interval.delete(0, tk.END)
                self.text_interval.insert(tk.END, str(interval))
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
                oil_to_show = max(1.0, oil_to_show)
                self.minimal_oil_to_show = oil_to_show
                self.text_minimal_oil_show.delete(0, tk.END)
                self.text_minimal_oil_show.insert(tk.END, str(oil_to_show))
                self.update_image_array(True)
                self.viewer.update_image()
            except ValueError:
                pass

        def toggle_start_stop(self):
            if self.is_running:
                self.stop_image_changes()
                self.btn_start_stop.config(state=DISABLED)
                self.after(100, self.wait_for_thread_to_unlock_buttons)
            else:
                self.start_image_changes()
                self.set_oil_spill_on_off.deselect()
                self.set_oil_spill_on_off.config(state=DISABLED)
                self.btn_save_checkpoint.config(state=DISABLED)
                self.text_minimal_oil_show.config(state=DISABLED)
                self.text_interval.config(state=DISABLED)
                self.text_oil_added.config(state=DISABLED)
                self.oil_spill_on_bool = False

        def start_image_changes(self):
            self.is_running = True
            self.update_occurred = False
            self.thread_finished = False
            self.btn_start_stop.configure(text="Stop")
            threading.Thread(target=self.threaded_function).start()
            self.job_id = self.after(self.interval, self.update_after)

        def stop_image_changes(self):
            self.is_running = False
            self.event_wait_for_gui_update.set()
            self.btn_start_stop.configure(text="Start")
            if self.job_id is not None:
                self.after_cancel(self.job_id)

        def wait_for_thread_to_unlock_buttons(self):
            if not self.thread_finished:
                self.after(100, self.wait_for_thread_to_unlock_buttons)
            else:
                self.update_image_array()
                self.update_occurred = False
                self.set_oil_spill_on_off.config(state=NORMAL)
                self.btn_save_checkpoint.config(state=NORMAL)
                self.text_minimal_oil_show.config(state=NORMAL)
                self.text_interval.config(state=NORMAL)
                self.text_oil_added.config(state=NORMAL)
                if not simulation_engine.is_finished():
                    self.btn_start_stop.config(state=NORMAL)

        def threaded_function(self):
            while self.is_running:
                simulation_engine.update(self.minimal_oil_to_show)
                self.update_occurred = True
                self.curr_iter += 1
                self.event_wait_for_gui_update.wait()
                self.event_wait_for_gui_update.clear()
            self.thread_finished = True

        def update_after(self):
            self.update_image_array()

        def update_image_array(self, full_update=False):
            if self.update_occurred and self.is_running or full_update:
                points_changed, points_removed = (simulation_engine.points_changed, simulation_engine.points_removed) if not full_update else (simulation_engine.world, [])
                if not full_update:
                    self.viewer.update_tooltip_text()

                for coords in points_changed:
                    if coords not in simulation_engine.world:
                        continue
                    pixel_color = simulation_engine.world[coords].pixel_color
                    self.full_img.putpixel((coords[0], coords[1]), pixel_color)

                for coords in points_removed:
                    if coords in simulation_engine.lands:
                        var = InitialValues.LAND_COLOR
                    else:
                        var = InitialValues.SEA_COLOR
                    self.full_img.putpixel((coords[0], coords[1]), var)

                self.value_not_yet_processed = 0

            self.update_infobox()
            if simulation_engine.is_finished():
                self.btn_start_stop.config(state=DISABLED)
                if self.is_running:
                    self.toggle_start_stop()
                self.options_frame.grid_remove()
                self.bottom_frame.grid()
                return

            if self.is_running:
                if self.update_occurred:
                    self.update_occurred = False
                    self.viewer.update_image()
                    self.event_wait_for_gui_update.set()
                self.job_id = self.after(self.interval, self.update_after)

        def update_infobox(self):
            self.infobox_current_iteration.configure(text=str(self.curr_iter))
            self.infobox_simulation_time.configure(text=generate_string_for_displaying_time(simulation_engine.total_time))

            self.update_oil_amount_infobox()
            self.update_idletasks()

        def update_oil_amount_infobox(self):
            global_oil_amount_sea, global_oil_amount_land = simulation_engine.get_oil_amounts()
            global_oil_amount_sea += self.value_not_yet_processed

            self.infobox_global_oil_amount_sea.configure(text=generate_string_for_displaying_oil_amount(global_oil_amount_sea))
            self.infobox_global_oil_amount_land.configure(text=generate_string_for_displaying_oil_amount(global_oil_amount_land))

            self.infobox_dispersed_oil.configure(text=generate_string_for_displaying_oil_amount(simulation_engine.dispersed_oil))
            self.infobox_evaporated_oil.configure(text=generate_string_for_displaying_oil_amount(simulation_engine.evaporated_oil))
            self.infobox_oil_area.configure(text=f"{(len(simulation_engine.world) * InitialValues.point_side_size ** 2) / 10**6} km2")

        def update_zoom_infobox_value(self):
            val5 = f"{round(self.viewer.zoom_level / self.viewer.initial_zoom_level, 2)} times"
            self.infobox_current_zoom.configure(text=val5)

        def oil_spill_on_off(self):
            self.oil_spill_on_bool = not self.oil_spill_on_bool

        def save_checkpoint(self):
            simulation_engine.save_checkpoint(True)

    def get_data_processor() -> DataProcessor:
        sym_data_reader = DataReader()
        try: 
            sym_data_reader.add_all_from_dir(InitialValues.data_dir_path)
        except DataValidationException as ex:
            logging.error(f"Data validation exception: {ex}")
            exit(1)

        memorized_time_start = deepcopy(InitialValues.simulation_initial_parameters.time.min) 
        if InitialValues.data_preprocessor_initial_timestamp is not None:
            InitialValues.simulation_initial_parameters.time.min = deepcopy(InitialValues.data_preprocessor_initial_timestamp) 

        result = sym_data_reader.preprocess(deepcopy(InitialValues.simulation_initial_parameters))
        InitialValues.simulation_initial_parameters.time.min = memorized_time_start
        return result

    simulation_engine = simulation.SimulationEngine(get_data_processor())

    if points:
        initialize_points_from_checkpoint(points, simulation_engine)
    if oil_sources:
        simulation_engine.add_oil_sources(oil_sources)

    x_indices = simulation_engine.x_indices
    y_indices = simulation_engine.y_indices

    sea_color = np.array(InitialValues.SEA_COLOR, dtype=np.uint8)
    land_color = np.array(InitialValues.LAND_COLOR, dtype=np.uint8)

    image_array = np.full((InitialValues.point_side_lat_count, InitialValues.point_side_lon_count, 3), sea_color,
                          dtype=np.uint8)

    image_array[y_indices, x_indices, :] = land_color

    del simulation_engine.x_indices, simulation_engine.y_indices

    main_frame = create_frame(window, 0, 0, 1, 1, tk.N + tk.S + tk.E + tk.W, 5, 5)

    main_frame.rowconfigure(0, weight=5, uniform='row')
    main_frame.rowconfigure(1, weight=1, uniform='row')
    main_frame.columnconfigure(0, weight=2, uniform='column')
    main_frame.columnconfigure(1, weight=1, uniform='column')

    full_img = Image.fromarray(image_array)

    simulation_engine.simulation_image = full_img

    frame_controller = ImageChangeController(main_frame, full_img)

    initial_zoom_level = 1
    viewer = ImageViewer(main_frame, image_array.shape, frame_controller, initial_zoom_level, full_img)
    viewer.grid(row=0, column=0, sticky=tk.N + tk.S + tk.E + tk.W)
    frame_controller.set_viewer(viewer)

    frame_controller.update_image_array()
    viewer.update()
    viewer.update_image()
    window.protocol("WM_DELETE_WINDOW", lambda: stop_thread_on_closing(window, frame_controller))
