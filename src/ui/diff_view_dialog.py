import tkinter as tk
import tkinter.ttk as ttk

from tkinter.scrolledtext import ScrolledText
from tkinter.font import Font

from tkinter.messagebox import showerror

import subprocess


class DiffViewDialog(tk.Toplevel):
    def __init__(self, master, initial_text, diff_left_path, diff_right_path, file_name, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title("Changes made to " + file_name)

        self.iconbitmap("icon.ico")

        self.master = master
        self.diff_left_path = diff_left_path.replace("\\", "/")
        self.diff_right_path = diff_right_path.replace("\\", "/")

        self.rowconfigure(0, weight=10)
        self.rowconfigure(1, weight=0)
        self.columnconfigure(0, weight=1)

        self.text_frame = ttk.Frame(self, style="MY.TFrame")
        self.text_frame.grid(row=0, column=0, sticky=tk.NW + tk.SE)

        self.text_frame.rowconfigure(0, weight=1)
        self.text_frame.columnconfigure(0, weight=1)

        font = Font(size=13)
        text_area = ScrolledText(self.text_frame, font=font, width=100)
        text_area.grid(row=0, column=0, sticky=tk.NW + tk.SE)

        text_area.insert(tk.END, initial_text)
        text_area.configure(state="disabled")

        self.buttons_frame = ttk.Frame(self)
        self.buttons_frame.grid(row=1, sticky=tk.EW)

        self.buttons_frame.columnconfigure(0, weight=1)
        self.buttons_frame.rowconfigure(0, weight=0)

        ttk.Button(self.buttons_frame, text="Close", command=self.destroy).grid(row=0, column=0, sticky=tk.SE, pady=10, padx=20)
        ttk.Button(self.buttons_frame, text="View with WinMerge", command=self.open_with_winmerge).grid(row=0, column=0, sticky=tk.SE, pady=10, padx=110)

        # Set to be on top of the main window
        self.transient(master)
        # Hijack all commands from the master (clicks on the main window are ignored)
        self.grab_set()
        # # Pause anything on the main window until this one closes
        master.wait_window(self)

    def open_with_winmerge(self):
        try:
            subprocess.Popen(["winmergeu", self.diff_left_path, self.diff_right_path])
        except Exception as e:
            msg = f"Please make sure WinMerge is in your PATH, and that the backup XML and updated XML are still available.\n\n" + str(e)
            showerror("Unable to open WinMerge", msg)
