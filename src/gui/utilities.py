import tkinter as tk
from tkinter import filedialog

from data.utilities import kelvins_to_celsius
from simulation import simulation


def get_tooltip_text(point: simulation.Point) -> str:
    return f"""Oil mass: {point.oil_mass: .2f}kg
--------------------
Wind speed N: {point.wind_velocity[0]: .2f}m/s
Wind speed E: {point.wind_velocity[1]: .2f}m/s
Current speed N: {point.wave_velocity[0]: .2f}m/s
Current speed E: {point.wave_velocity[1]: .2f}m/s
Temperature: {kelvins_to_celsius(point.temperature): .2f}°C"""


def create_frame(parent: tk.Frame, row: int, column: int, rowspan: int = 1, columnspan: int = 1,
                 sticky: str = tk.N + tk.S, padx: int = 0, pady: int = 0, relief_style=tk.FLAT) -> tk.Frame:
    frame = tk.Frame(parent, relief=relief_style, borderwidth=1)
    frame.grid(row=row, column=column, padx=padx, pady=pady, rowspan=rowspan, columnspan=columnspan, sticky=sticky)
    return frame


def create_label(parent: tk.Frame, text: str = "", font: tuple[str, int, str] = ("Arial", 14, "bold"),
                 padx: int = 10, pady: int = 5) -> tk.Label:
    label = tk.Label(parent, text=text, font=font, padx=padx, pady=pady)
    return label


def create_label_pack(parent: tk.Frame, text: str = "", font: tuple[str, int, str] = ("Arial", 14, "bold"),
                      padx: int = 10, pady: int = 5, side=tk.TOP) -> tk.Label:
    label = create_label(parent, text, font, padx, pady)
    label.pack(side=side)
    return label


def create_label_grid_parameter_screen(parent: tk.Frame) -> tk.Label:
    return create_label_grid(parent, "Default value", 2, 0, ("Arial", 8, "bold"))


def create_label_grid(parent: tk.Frame, text: str, row: int = 0, column: int = 0,
                      font: tuple[str, int, str] = ("Arial", 12, "bold"), padx: int = 10, pady: int = 5,
                      rowspan: int = 1, columnspan: int = 1, sticky: str = tk.N + tk.S, padx_grid: int = 3,
                      pady_grid: int = 3) -> tk.Label:
    label = create_label(parent, text, font, padx, pady)
    label.grid(row=row, column=column, padx=padx_grid, pady=pady_grid, rowspan=rowspan, columnspan=columnspan,
               sticky=sticky)
    return label


def create_input_entry(parent: tk.Frame, width: int, text: str, validation_function) -> tk.Entry:
    input_widget = tk.Entry(parent, width=width)
    input_widget.insert(tk.END, str(text))
    input_widget.bind("<KeyPress>", lambda event: on_key_press(event, validation_function=validation_function))
    input_widget.bind("<FocusOut>", lambda event: on_focus_out(event, validation_function=validation_function))
    return input_widget


def create_input_entry_pack(parent: tk.Frame, width: int, text: str, validation_function, side=tk.BOTTOM) -> tk.Entry:
    input_widget = create_input_entry(parent, width, text, validation_function)
    input_widget.pack(side=side)

    return input_widget


def create_input_entry_grid(parent: tk.Frame, width: int, text: str, validation_function, row: int = 1,
                            column: int = 0, sticky: str = tk.N + tk.S, padx: int = 3, pady: int = 3) -> tk.Entry:
    input_widget = create_input_entry(parent, width, text, validation_function)
    input_widget.grid(row=row, column=column, padx=padx, pady=pady, sticky=sticky)

    return input_widget


def on_key_press(event, validation_function):
    if event.keysym == "Return":
        validation_function()


def on_focus_out(_, validation_function):
    validation_function()


def browse_button(target):
    filename = filedialog.askopenfilename()
    if filename:
        target.set(filename)

        
def browse_dir_button(target):
    dirname = filedialog.askdirectory()
    if dirname:
        target.set(dirname)


def resize_img_to_fit_frame(img, frame):
    w, h = img.size
    w_frame, h_frame = frame.winfo_width(), frame.winfo_height()

    if w / w_frame > h / h_frame:
        w_resize = w_frame
        h_resize = int(w_frame * (h / w))
    else:
        h_resize = h_frame
        w_resize = int(h_frame * (w / h))

    return img.resize((w_resize, h_resize))
