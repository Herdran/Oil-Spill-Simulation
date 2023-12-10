import logging
import threading
import tkinter as tk
from tkinter import DISABLED, NORMAL

import numpy as np
from PIL import Image, ImageTk

import simulation.simulation as simulation
from checkpoints import initialize_simulation_from_checkpoint
from color import rgba, blend_color, rgba_to_rgb
from constatnts import Constants as const
from data.data_processor import DataProcessor, DataReader, DataValidationException
from files import get_main_path
from gui.utilities import get_tooltip_text, create_frame, create_label_pack, create_input_entry_pack

SEA_COLOR = rgba(15, 10, 222)
LAND_COLOR = rgba(38, 166, 91)
OIL_COLOR = rgba(0, 0, 0)
LAND_WITH_OIL_COLOR = rgba(0, 100, 0)


def start_simulation(neighborhood, window, world_from_checkpoint=None, oil_sources=None):
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
                self.pan_x -= max(
                    (((self.image_array_width - (window_width / self.zoom_level)) - before_x) / 2) * self.zoom_level, 0)
                self.pan_y -= max(
                    (((self.image_array_height - (window_height / self.zoom_level)) - before_y) / 2) * self.zoom_level,
                    0)
            else:
                self.pan_x += max(
                    ((before_x - (self.image_array_width - (window_width / self.zoom_level))) / 2) * self.zoom_level, 0)
                self.pan_y += max(
                    ((before_y - (self.image_array_height - (window_height / self.zoom_level))) / 2) * self.zoom_level,
                    0)

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
                return
            if not self.image_change_controller.oil_spill_on_bool:
                return
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
            coord = (x, y)
            if not (0 <= x < self.image_array.shape[1] and 0 <= y < self.image_array.shape[0]):
                self.hide_tooltip()
                return
            if coord not in engine.world:
                self.show_tooltip(event.x_root, event.y_root, f"Oil mass: {0: .2f}kg")
            else:
                point = engine.world[(x, y)]
                self.show_tooltip(event.x_root, event.y_root, get_tooltip_text(point))

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
            self.iter_as_sec = const.iter_as_sec
            self.viewer = None
            self.value_not_yet_processed = 0
            self.oil_spill_on_bool = True

            self.options_frame = create_frame(window, 1, 0, 1, 2, tk.N + tk.S, 5, 5)

            self.options_frame.columnconfigure(0, weight=2)
            self.options_frame.columnconfigure(1, weight=2)
            self.options_frame.columnconfigure(2, weight=2)
            self.options_frame.columnconfigure(3, weight=2)
            self.options_frame.columnconfigure(4, weight=1)
            self.options_frame.columnconfigure(5, weight=1)

            interval_frame = create_frame(self.options_frame, 0, 0, 1, 1, tk.N + tk.S, 5, 5)
            oil_added_frame = create_frame(self.options_frame, 0, 2, 1, 1, tk.N + tk.S, 5, 5)
            minimal_oil_value_to_show_frame = create_frame(self.options_frame, 0, 3, 1, 1, tk.N + tk.S, 5, 5)
            start_stop_frame = create_frame(self.options_frame, 0, 4, 1, 2, tk.N + tk.S, 5, 5)

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

            self.btn_start_stop = tk.Button(start_stop_frame, text="Start", width=10, command=self.toggle_start_stop)
            self.btn_start_stop.pack(side=tk.TOP, padx=5, pady=5)

            self.text_interval = create_input_entry_pack(interval_frame, 10, str(self.interval / 1000),
                                                         self.validate_interval)
            self.text_oil_added = create_input_entry_pack(oil_added_frame, 10, str(self.oil_to_add_on_click),
                                                          self.validate_oil_to_add)
            self.text_minimal_oil_show = create_input_entry_pack(minimal_oil_value_to_show_frame, 10,
                                                                 str(self.minimal_oil_to_show),
                                                                 self.validate_minimal_oil_to_show)

            self.infoboxes_frame = create_frame(window, 0, 1, 1, 1, tk.N + tk.S + tk.E, 5, 5)

            frame_infoboxes_labels = create_frame(self.infoboxes_frame, 0, 0, 1, 1, tk.N + tk.S + tk.E, 5, 5)

            create_label_pack(frame_infoboxes_labels, "Current iteration")
            create_label_pack(frame_infoboxes_labels, "Simulation time")
            create_label_pack(frame_infoboxes_labels, "Global oil amount [sea]")
            create_label_pack(frame_infoboxes_labels, "Global oil amount [land]")
            create_label_pack(frame_infoboxes_labels, "Current zoom")

            frame_infoboxes_values = create_frame(self.infoboxes_frame, 0, 1, 1, 1, tk.N + tk.S + tk.E, 5, 5)

            self.infobox1_values_label = create_label_pack(frame_infoboxes_values)
            self.infobox2_values_label = create_label_pack(frame_infoboxes_values)
            self.infobox3_values_label = create_label_pack(frame_infoboxes_values)
            self.infobox4_values_label = create_label_pack(frame_infoboxes_values)
            self.infobox5_values_label = create_label_pack(frame_infoboxes_values, "1.0")

            self.bottom_frame = create_frame(window, 1, 0, 1, 2, tk.N + tk.S, 5, 5)

            create_label_pack(self.bottom_frame, "Simulation finished!")
            self.bottom_frame.grid_remove()

            self.update_image_array()
            self.update_infobox()

        def set_viewer(self, viewer):
            self.viewer = viewer

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
                deleted = engine.update()
                for coords in deleted:
                    self.image_array[coords[1]][coords[0]] = rgba_to_rgb(
                        LAND_COLOR) if coords in engine.lands else rgba_to_rgb(SEA_COLOR)
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

        return sym_data_reader.preprocess(const.simulation_initial_parameters)

    engine = simulation.SimulationEngine(get_data_processor(), neighborhood)

    if world_from_checkpoint:
        initialize_simulation_from_checkpoint(world_from_checkpoint, engine.initial_values, engine)
    if oil_sources:
        engine.add_oil_sources(oil_sources)

    image_array = np.array(
        [rgba_to_rgb(LAND_COLOR) if (j, i) in engine.lands else rgba_to_rgb(SEA_COLOR) for i in
         range(const.point_side_count) for j in
         range(const.point_side_count)]).reshape((const.point_side_count, const.point_side_count, 3)).astype(np.uint8)

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
