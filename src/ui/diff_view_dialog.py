import tkinter as tk
import tkinter.ttk as ttk

from tkinter.scrolledtext import ScrolledText
from tkinter.font import Font

from tkinter.messagebox import askokcancel

import os


class DiffViewDialog(tk.Toplevel):
    def __init__(self, master, initial_text, diff_left_path, diff_right_path, file_name, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title("Changes made to " + file_name)

        # self.minsize(500, 300)
        # self.maxsize(500, 300)
        # self.resizable(False, False)
        self.iconbitmap("icon.ico")

        self.master = master

        self.rowconfigure(0, weight=10)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        self.text_frame = ttk.Frame(self, style="MY.TFrame")
        self.text_frame.grid(row=0, column=0)

        self.text_frame.rowconfigure(0, weight=1)
        self.text_frame.columnconfigure(0, weight=1)

        font = Font(size=13)
        text_area = ScrolledText(self.text_frame, font=font, width=100, height=20)
        text_area.grid(row=0, sticky=tk.NW + tk.SE)

        text_area.insert(tk.END, initial_text)
        text_area.configure(state="disabled")

        self.buttons_frame = ttk.Frame(self)
        self.buttons_frame.grid(row=1, sticky=tk.EW)

        self.buttons_frame.columnconfigure(0, weight=1)

        def show_diff():
            left_size = os.path.getsize(diff_left_path)
            right_size = os.path.getsize(diff_right_path)

            if left_size > 1_000_000 or right_size > 1_000_000:
                msg = "One or both of the files are greater than 1MB in size. Trying to diff large files will cause the program to crash."
                result = askokcancel("Are you sure?", msg)

                if not result:
                    return

        ttk.Button(self.buttons_frame, text="Close", command=self.destroy).grid(row=0, column=0, sticky=tk.SE, pady=10, padx=20)

        # Set to be on top of the main window
        self.transient(master)
        # Hijack all commands from the master (clicks on the main window are ignored)
        self.grab_set()
        # # Pause anything on the main window until this one closes
        master.wait_window(self)
