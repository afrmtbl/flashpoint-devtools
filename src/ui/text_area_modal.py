import tkinter as tk
import tkinter.ttk as ttk

from tkinter.scrolledtext import ScrolledText
from tkinter.font import Font


class TextAreaModal(tk.Toplevel):
    def __init__(self, master, initial_title, initial_text, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title(initial_title)

        self.iconbitmap("icon.ico")

        self.master = master

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

    def raise_to_top(self):
        # Set to be on top of the main window
        self.transient(self.master)
        # Hijack all commands from the master (clicks on the main window are ignored)
        self.grab_set()
        # # Pause anything on the main window until this one closes
        self.master.wait_window(self)
