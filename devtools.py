import tkinter as tk
import tkinter.ttk as ttk

from src.ui.metadata_editor import MetadataEditorTab

WINDOW_WIDTH = 550
WINDOW_HEIGHT = 200

root = tk.Tk()
root.title("Flashpoint DevTools")

root.iconbitmap("icon.ico")

root.minsize(WINDOW_WIDTH, WINDOW_HEIGHT)
root.maxsize(WINDOW_WIDTH, WINDOW_HEIGHT)
root.resizable(False, False)

root.rowconfigure(0, weight=1)
root.columnconfigure(0, weight=1)

style = ttk.Style()
style.configure("MY.TFrame", background="white")
style.configure("MY.TLabel", background="white")

style.configure("WARN.TLabel", background="white", foreground="red")

note = ttk.Notebook(root)

tab1 = MetadataEditorTab(note, style="MY.TFrame")

note.add(tab1, text="Metadata Editor", padding="24px 0px")
note.grid(sticky=tk.NW + tk.SE)

root.mainloop()
