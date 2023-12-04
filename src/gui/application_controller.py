import tkinter as tk

from gui.parameters_screen import start_initial_menu


def run():
    DEFAULT_WINDOW_WIDTH = 1280
    DEFAULT_WINDOW_HEIGHT = 720

    window = tk.Tk()
    window.geometry(f"{DEFAULT_WINDOW_WIDTH}x{DEFAULT_WINDOW_HEIGHT}")
    window.title('Oil Spill Simulation')
    window.rowconfigure(0, weight=1, uniform='row')
    window.columnconfigure(0, weight=1, uniform='column')

    start_initial_menu(window)

    window.mainloop()
