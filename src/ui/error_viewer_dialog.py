import tkinter as tk
import tkinter.ttk as ttk

from src.ui.text_area_modal import TextAreaModal

from tkinter.messagebox import showinfo, askokcancel, showerror

from typing import List
import os

from shutil import copy2


class ErrorViewerDialog(TextAreaModal):
    def __init__(self, backup_file_names: List[str], backup_directory: str, dest_directory: str, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.backup_file_names = backup_file_names
        self.backup_directory = backup_directory
        self.dest_directory = dest_directory

        self.restored_backups = False

        if len(self.backup_file_names) > 0 and self.backup_directory and self.dest_directory:
            self.restore_button = ttk.Button(self.buttons_frame, text="Restore backups", command=self.undo_changes)
            self.restore_button.grid(row=0, column=0, sticky=tk.SE, pady=10, padx=110)
        else:
            self.label = ttk.Label(self.buttons_frame, text="No changes were made to any XML files...", font="TkDefaultFont 12")
            self.label.grid(row=0, column=0, sticky=tk.W, padx=20)

        self.raise_to_top()

    def undo_changes(self):

        result = askokcancel("Are you sure?", "The following files will be restored from backup: \n\n" + "\n".join(self.backup_file_names), parent=self)
        if result:
            try:
                for file in self.backup_file_names:
                    current_path = os.path.join(self.backup_directory, file)
                    new_path = os.path.join(self.dest_directory, file)
                    copy2(current_path, new_path)
                    os.remove(current_path)
                    self.restored_backups = True
            except Exception as e:
                showerror("Error occurred while restoring backups", str(e), parent=self)
                return

            showinfo("Backups", "Backups restored successfully", parent=self)

            self.restore_button.configure(state=tk.DISABLED)
