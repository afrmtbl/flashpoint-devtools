import tkinter as tk
import tkinter.ttk as ttk

from src.tabs.metadata_editor import MetadataEditorTab

# not complete yet
# from src.tabs.missing_files import MissingFilesTab

WINDOW_WIDTH = 460
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

note = ttk.Notebook(root)

tab1 = MetadataEditorTab(note, style="MY.TFrame")
# tab2 = MissingFilesTab(note, style="MY.TFrame")

note.add(tab1, text="Metadata Editor", padding="24px 0px")
# note.add(tab2, text="Missing Files", padding="24px 0px")
note.grid(sticky=tk.NW+tk.SE)

root.mainloop()