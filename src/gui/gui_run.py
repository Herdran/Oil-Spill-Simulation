import tkinter as tk

from gui.parameters_screen import start_initial_menu


def run():
    default_window_width = 1280
    default_window_height = 720

    window = tk.Tk()
    window.geometry(f"{default_window_width}x{default_window_height}")
    window.title('Oil Spill Simulation')
    window.rowconfigure(0, weight=1, uniform='row')
    window.columnconfigure(0, weight=1, uniform='column')

    start_initial_menu(window)

    window.mainloop()
