import tkinter as tk
import tkinter.ttk as ttk

from tkinter.filedialog import askopenfilename, asksaveasfile, askdirectory
import tkinter.messagebox

import threading
import os
from shutil import copy2

from src.util.changes_parser import ChangesParser

from src.util.xml_updater import parse_changes_file, get_updated_xml, UpdaterExceptions
from src.util.xml_updater import explain_changes

from src.ui.diff_view_dialog import DiffViewDialog

ERROR_LOADING_ELEMENTS_WHITELIST = False

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.normpath(ROOT_DIR + "/../..")
try:
    with open(BASE_DIR + "/elements_whitelist.txt", encoding="utf8") as file:
        create_elements_whitelist = [line.strip() for line in file if line.strip()]
except FileNotFoundError:
    create_elements_whitelist = []
    ERROR_LOADING_ELEMENTS_WHITELIST = True


def backup_xml_file(current_file_path, backup_file_name):
    backups_directory = BASE_DIR + "/xmlbackups"
    if not os.path.isdir(backups_directory):
        os.mkdir(backups_directory)

    new_path = f"{backups_directory}/{backup_file_name}"
    copy2(current_file_path, new_path)

    return new_path


class MetadataEditorTab(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.generating_xml = False

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=10)
        self.columnconfigure(2, weight=1)

        self.add_widgets()

        if ERROR_LOADING_ELEMENTS_WHITELIST:
            tkinter.messagebox.showerror("Elements Whitelist Not Found", "The elements_whitelist.txt could not be found. Running with empty whitelist.")

        self.view_diff_prompts = []

        if os.path.exists(BASE_DIR + "/last_xml_directory.txt"):
            with open(BASE_DIR + "/last_xml_directory.txt", "r", encoding="utf8") as file:
                self.xml_path.delete(0, tk.END)
                self.xml_path.insert(0, file.read())

    def add_widgets(self):
        description = ttk.Label(self, text="Quickly edit XML files from the specified directory using a list of changes", style="MY.TLabel")
        description.grid(columnspan=3, pady=(5, 10))

        ttk.Label(self, text="XML Directory", style="MY.TLabel").grid(row=1, column=0)

        self.xml_path = ttk.Entry(self)
        self.xml_path.grid(row=1, column=1, sticky=tk.EW, pady=(5, 5))

        ttk.Button(self, text="Browse", command=self.choose_xml_directory).grid(row=1, column=2, sticky=tk.E)

        ttk.Label(self, text="Changes File", style="MY.TLabel").grid(row=2, column=0)
        self.change_file_path = ttk.Entry(self)
        self.change_file_path.grid(row=2, column=1, sticky=tk.EW, pady=(5, 5))

        self.browse_changes_button = ttk.Button(self, text="Browse", command=self.choose_changes_file)
        self.browse_changes_button.grid(row=2, column=2, sticky=tk.E)

        self.help_button = ttk.Button(self, text="Help", command=self.show_help)
        self.help_button.grid(row=4, column=1, sticky=tk.E, pady=20)

        self.generate_button = ttk.Button(self, text="Generate XML", command=self.threaded_update)
        self.generate_button.grid(row=4, column=2, sticky=tk.E, pady=20)

        if ERROR_LOADING_ELEMENTS_WHITELIST or len(create_elements_whitelist) < 1:
            whitelist_warning = ttk.Label(self, text="Running with empty elements whitelist...", style="WARN.TLabel", font="TkDefaultFont 10 bold")
            whitelist_warning.grid(row=4, column=0, columnspan=3, sticky=tk.W)

    def choose_xml_directory(self):
        directory = askdirectory()
        self.xml_path.delete(0, tk.END)
        self.xml_path.insert(0, directory)

    def choose_changes_file(self):
        file = askopenfilename()
        self.change_file_path.delete(0, tk.END)
        self.change_file_path.insert(0, file)

    def update_metadata_new(self, xml_directory, changes_file_path):

        def freeze():
            self.generating_xml = True
            self.generate_button.configure(state=tk.DISABLED)

        def unfreeze():
            self.generating_xml = False
            self.generate_button.configure(state=tk.NORMAL)

        if not os.path.isdir(xml_directory):
            tkinter.messagebox.showerror("Directory not found", f"Invalid XML directory: \'{xml_directory}\'")
            self.generating_xml = False
            return
        else:
            with open(BASE_DIR + "/last_xml_directory.txt", "w", encoding="utf8") as file:
                file.write(xml_directory)

        if not os.path.isfile(changes_file_path):
            tkinter.messagebox.showerror("File not found", f"Invalid change file path: \'{changes_file_path}\'")
            self.generating_xml = False
            return

        freeze()
        self.view_diff_prompts.clear()

        try:
            changes = parse_changes_file(changes_file_path)
        except UpdaterExceptions.InvalidGameId as e:
            tkinter.messagebox.showerror("Invalid Game ID", str(e))
        except UpdaterExceptions.ForbiddenElementChange as e:
            tkinter.messagebox.showerror("Forbidden Element Change", str(e))

        platform_xml_files = os.listdir(xml_directory)
        platform_xml_files = [
            file for file in platform_xml_files
            if os.path.isfile(os.path.join(xml_directory, file)) and file.endswith(".xml")
        ]

        for platform_xml in platform_xml_files:
            # All games have been found and updated
            # No need to keep looking in the rest of the files
            if len(changes) == 0:
                break

            file_path = os.path.join(xml_directory, platform_xml)

            print("Looking in " + platform_xml)

            try:
                updated_xml, changed_games = get_updated_xml(changes, file_path, create_elements_whitelist, raise_on_missing_game=False)

                file_changes = {}

                if len(changed_games) > 0:

                    for game in changed_games:
                        file_changes[game] = changes[game]
                        del changes[game]

                    backup_path = backup_xml_file(file_path, platform_xml)

                    updated_xml.write(file_path, encoding="utf8", pretty_print=True)

                    explanation = explain_changes(file_changes)

                    self.view_diff_prompts.append((backup_path, file_path, explanation, platform_xml))

            except UpdaterExceptions.MissingElement as e:
                tkinter.messagebox.showerror("Missing element", str(e))
            except UpdaterExceptions.MissingElementValue as e:
                tkinter.messagebox.showerror("Missing element value", str(e))

        if len(changes):
            tkinter.messagebox.showerror("Unable to find games", "The following games could not be found and were not changed:\n  " + "\n  ".join(changes.keys()))

        for backup_path, file_path, explanation, platform_xml in self.view_diff_prompts:
            DiffViewDialog(self, explanation, backup_path, file_path, platform_xml)

        self.change_file_path.delete(0, tk.END)
        unfreeze()

    def threaded_update(self):

        if not self.generating_xml:

            thread = threading.Thread(
                target=self.update_metadata_new,
                args=(
                    self.xml_path.get(),
                    self.change_file_path.get()
                )
            )

            thread.start()

    def show_help(self):

        left = "C:\\Users\\afrm\\Desktop\\flashpoint-devtools\\xmlbackups\\Flash.xml"
        right = "C:\\Users\\afrm\\Desktop\\fps\\data\\games\\Flash.xml"
        DiffViewDialog(self, "Hello there!", left, right, "test.xml")


#         text = """
# Basically a batch XML element text updater

# The changes file must be in the following format:

# GAME $GAME_ID
# $ELEMENT_NAME: New Value

# For example:
# GAME dbde64aa-fbd7-4837-bba5-63d923092486
#     Title: Swag
#     Genre: Adventure, Point'n'Click
#     Publisher: Newgrounds.com

# GAME ea84e831-ee4f-44ec-b769-b657c8ffa8e3
#     Genre: Puzzle, Tetris, Physics

# Any leading and trailing whitespace is automatically stripped, so it can be used to increase readability"""

#         tkinter.messagebox.showinfo("Help", text)
