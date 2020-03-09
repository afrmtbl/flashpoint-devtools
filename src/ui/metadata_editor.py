import tkinter as tk
import tkinter.ttk as ttk

from tkinter.filedialog import askopenfilename, askdirectory
import tkinter.messagebox

import threading
import os
from shutil import copy2

from src.util.xml_updater import ChangesParser, XmlUpdater, explain_changes

from src.ui.diff_view_dialog import DiffViewDialog
from src.ui.error_viewer_dialog import ErrorViewerDialog

try:
    import winsound
except ImportError:
    pass


ERROR_LOADING_ELEMENTS_WHITELIST = False

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.normpath(ROOT_DIR + "/../..")

BACKUPS_DIR = BASE_DIR + "/xmlbackups"
try:
    with open(BASE_DIR + "/elements_whitelist.txt", encoding="utf8") as file:
        create_elements_whitelist = [line.strip() for line in file if line.strip()]
except FileNotFoundError:
    create_elements_whitelist = []
    ERROR_LOADING_ELEMENTS_WHITELIST = True


def backup_xml_file(current_file_path, backup_file_name):
    if not os.path.isdir(BACKUPS_DIR):
        os.mkdir(BACKUPS_DIR)

    new_path = f"{BACKUPS_DIR}/{backup_file_name}"
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

    def update_metadata(self, xml_directory, changes_file_path):

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

        changes = {}

        try:
            changes = ChangesParser.parse_changes_file(changes_file_path)
        except ChangesParser.InvalidGameId as e:
            tkinter.messagebox.showerror("Invalid Game ID", str(e))
            unfreeze()
            return
        except ChangesParser.ForbiddenElementChange as e:
            tkinter.messagebox.showerror("Forbidden Element Change", str(e))
            unfreeze()
            return
        except ChangesParser.NotEnoughDocuments as e:
            tkinter.messagebox.showerror("Invalid YAML", str(e))
            unfreeze()
            return
        except ChangesParser.DuplicateGameId as e:
            tkinter.messagebox.showerror("Invalid YAML", str(e))
            unfreeze()
            return
        except Exception as e:
            tkinter.messagebox.showerror("Error while parsing changes file", str(e))
            unfreeze()
            return

        platform_xml_files = os.listdir(xml_directory)
        platform_xml_files = [
            file for file in platform_xml_files
            if os.path.isfile(os.path.join(xml_directory, file)) and file.endswith(".xml")
        ]

        view_diff_prompts = []
        view_error_prompts = []
        files_backed_up = []

        for platform_xml in platform_xml_files:
            # All games have been found and updated
            # No need to keep looking in the rest of the files
            if len(changes) == 0:
                break

            file_path = os.path.join(xml_directory, platform_xml)

            updater = XmlUpdater()
            updated_xml, games_changed, games_failed = updater.get_updated_xml(changes, file_path, create_elements_whitelist)

            for game in games_failed:
                view_error_prompts.append(game)
                del changes[game.game_id]

            changes_in_file = {}

            if len(games_changed) > 0:

                for game in games_changed:
                    changes_in_file[game] = changes[game]
                    del changes[game]

                backup_path = backup_xml_file(file_path, platform_xml)
                files_backed_up.append(platform_xml)

                updated_xml.write(file_path, encoding="utf8", pretty_print=True)
                explanation = explain_changes(changes_in_file)
                view_diff_prompts.append((backup_path, file_path, explanation, platform_xml))

        restored_backups = False

        if len(view_error_prompts) or len(changes):
            text = "\n\n".join([f"{e.game_id}\n      {str(e)}" for e in view_error_prompts])
            missing_text = "\n\n".join([f"Game with ID \'{game_id}\' could not be found" for game_id in changes])

            try:
                winsound.PlaySound("SystemHand", winsound.SND_ALIAS + winsound.SND_ASYNC)
            except NameError:
                pass

            title = "One or more errors occurred while updating the XML"
            restored_backups = ErrorViewerDialog(files_backed_up, BACKUPS_DIR, xml_directory, self, title, missing_text + "\n\n" + text).restored_backups
            # tkinter.messagebox.showerror("Unable to find games", "The following games could not be found and were not changed:\n  " + "\n  ".join(changes.keys()))

        if not restored_backups:
            for backup_path, file_path, explanation, platform_xml in view_diff_prompts:
                DiffViewDialog(backup_path, file_path, self, f"Changes made to {platform_xml}", explanation)

        self.change_file_path.delete(0, tk.END)
        unfreeze()

    def threaded_update(self):

        if not self.generating_xml:

            thread = threading.Thread(
                target=self.update_metadata,
                args=(
                    self.xml_path.get(),
                    self.change_file_path.get()
                )
            )

            thread.start()

    def show_help(self):

        text = """
Basically a batch XML element text updater

The changes file must be in the following format:

GAME: $GAME_ID
$ELEMENT_NAME: New Value

Each new game, except for the last, should be followed by three dashes (---). The first game should not be preceded by three dashes.

For example:
GAME: dbde64aa-fbd7-4837-bba5-63d923092486
  Title: Swag
  Genre: Adventure; Point'n'Click
  Publisher: Newgrounds.com

---

GAME: ea84e831-ee4f-44ec-b769-b657c8ffa8e3
Genre:
  - Puzzle
  - Tetris
  - Physics
"""

        tkinter.messagebox.showinfo("Help", text)
