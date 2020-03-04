import tkinter as tk
import tkinter.ttk as ttk

from tkinter.messagebox import showerror

import subprocess

from src.ui.text_area_modal import TextAreaModal


class DiffViewDialog(TextAreaModal):
    def __init__(self, diff_left_path, diff_right_path, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.diff_left_path = diff_left_path.replace("\\", "/")
        self.diff_right_path = diff_right_path.replace("\\", "/")

        ttk.Button(self.buttons_frame, text="View with WinMerge", command=self.open_with_winmerge).grid(row=0, column=0, sticky=tk.SE, pady=10, padx=110)

        self.raise_to_top()

    def open_with_winmerge(self):
        try:
            subprocess.Popen(["winmergeu", self.diff_left_path, self.diff_right_path])
        except Exception as e:
            msg = f"Please make sure WinMerge is in your PATH, and that the backup XML and updated XML are still available.\n\n" + str(e)
            showerror("Unable to open WinMerge", msg)
