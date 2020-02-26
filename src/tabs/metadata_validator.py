import tkinter as tk
import tkinter.ttk as ttk

# from tkinter.filedialog import askopenfilename, asksaveasfile
import tkinter.messagebox

# import threading
import os
import xml.etree.ElementTree as ET
from ..util.metadata_validation import find_invalid_element_values, find_invalid_genre_values, check_if_element_exists
from ..util.metadata_validation import MissingElement, MissingElementText, ElementTextFailedTest

import subprocess


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


class MetadataValidatorTab(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.tree_item_ignore_clicks = []

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=10)
        self.columnconfigure(2, weight=1)

        self.add_widgets()

        # self.scan_platform_xmls()

    def add_widgets(self):
        description = ttk.Label(self, text="Scan platform XMLs for metadata issues", style="MY.TLabel")
        description.grid(columnspan=3, sticky="W", pady=(5, 10))

        self.tree = ttk.Treeview(self)
        self.tree.bind("<Double-Button-1>", self.double_click_item)

        self.tree["columns"] = ("value", "type")

        self.tree.column("#0", width=120)
        self.tree.column("value", width=50)
        self.tree.column("type", width=50)

        self.tree.heading("#0", text="Game ID", anchor=tk.W)
        self.tree.heading("value", text="Info", anchor=tk.W)
        self.tree.heading("type", text="File", anchor=tk.W)

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=1, column=2, sticky=tk.NS + tk.E)

        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=1, column=1, sticky=tk.NW + tk.SE)

        buttons_frame = ttk.Frame(self, style="MY.TFrame")

        self.help_button = ttk.Button(buttons_frame, text="Help", command=self.show_help)
        self.help_button.grid(sticky=tk.E, pady=20, padx=10, row=0, column=2)

        self.generate_button = ttk.Button(buttons_frame, text="Scan", command=self.scan_platform_xmls)
        self.generate_button.grid(sticky=tk.E, row=0, column=3)

        buttons_frame.grid(row=3, columnspan=3, sticky=tk.E)

    def double_click_item(self, event):
        item_id = self.tree.identify_row(event.y)
        item = self.tree.item(item_id)

        if item_id not in self.tree_item_ignore_clicks:
            file_dir = "C:/Users/afrm/Desktop/fps/data/games/"
            file_name = item["values"][1]

            file_path = file_dir + file_name

            game_id = item["text"]

            with open(file_path, "r", encoding="utf8") as file:
                current_line = 1
                found_line = False

                for line in file:
                    if game_id in line:
                        found_line = True
                        break

                    current_line += 1

                if found_line:
                    command = ["subl.exe", f"{file_path}:{current_line}"]
                    print(command)
                    subprocess.run(command)
                else:
                    print(f"Unable to find {game_id} in {file_path}")

    def scan_platform_xmls(self):

        self.tree.delete(*self.tree_item_ignore_clicks)

        status_folder = self.tree.insert("", 1, text="Invalid Status Element", values=("", ""), open=False)
        genre_folder = self.tree.insert("", 1, text="Invalid Genre Element", values=("", ""), open=False)
        platform_folder = self.tree.insert("", 1, text="Invalid Platform Element", values=("", ""), open=False)
        command_line_folder = self.tree.insert("", 1, text="Invalid CommandLine Element", values=("", ""), open=False)

        self.tree_item_ignore_clicks.extend((status_folder, genre_folder, platform_folder, command_line_folder))

        def check_element_basic(folder_id, element_name, valid_statuses):
            for result in find_invalid_element_values(xml_tree, element_name, valid_statuses):
                if isinstance(result, MissingElement):
                    game_id = result.game_id
                    item = self.tree.insert(folder_id, "end", text=game_id, values=(f"Missing <{element_name}> element", file))
                    self.tree.move(item, folder_id, 0)

                elif isinstance(result, MissingElementText):
                    game_id = result.game_id
                    item = self.tree.insert(folder_id, "end", text=game_id, values=("(empty)", file))
                    self.tree.move(item, folder_id, 0)
                else:
                    game_id, value = result
                    self.tree.insert(folder_id, "end", text=game_id, values=(value, file))

            children = len(self.tree.get_children(folder_id))

            self.tree.item(folder_id, text=f"Invalid {element_name} Element ({children})")

        for file in os.listdir("C:/Users/afrm/Desktop/fps/data/games"):

            if file.endswith(".xml"):
                file_path = "C:/Users/afrm/Desktop/fps/data/games/" + file
                xml_tree = ET.parse(file_path)

                for result in find_invalid_genre_values(xml_tree):
                    if isinstance(result, MissingElement):
                        game_id = result.game_id
                        item = self.tree.insert(genre_folder, "end", text=game_id, values=("Missing <Genre> element", file))
                        self.tree.move(item, genre_folder, 0)

                    elif isinstance(result, MissingElementText):
                        game_id = result.game_id
                        item = self.tree.insert(genre_folder, "end", text=game_id, values=("(empty)", file))
                        self.tree.move(item, genre_folder, 0)
                    else:
                        game_id, invalid_genres = result
                        invalid_genres = ",".join(invalid_genres)
                        invalid_genres = "(empty)" if not invalid_genres else invalid_genres

                        self.tree.insert(genre_folder, "end", text=game_id, values=(invalid_genres, file))

                children = len(self.tree.get_children(genre_folder))
                self.tree.item(genre_folder, text=f"Invalid Genre Element ({children})")

                valid_platforms = ("Flash", "Shockwave", "HTML5", "Java", "Unity", "Silverlight", "3DVIA Player", "3D Groove GX", "ActiveX", "Authorware", "ShiVa3D", "GoBit", "PopCap Plugin")
                check_element_basic(platform_folder, "Platform", valid_platforms)
                check_element_basic(status_folder, "Status", ("Playable", "Partial", "Hacked"))

                el_name = "CommandLine"
                for result in check_if_element_exists(xml_tree, el_name, lambda txt: not txt.startswith("https://")):
                    if isinstance(result, MissingElement):
                        game_id = result.game_id
                        item = self.tree.insert(command_line_folder, "end", text=game_id, values=(f"Missing <{el_name}> element", file))
                        self.tree.move(item, command_line_folder, 0)

                    elif isinstance(result, ElementTextFailedTest):
                        game_id = result.game_id

                        item = self.tree.insert(command_line_folder, "end", text=game_id, values=(f"<{el_name}> failed test", file))
                        self.tree.move(item, command_line_folder, 0)
                    else:
                        if not result:
                            self.tree.insert(command_line_folder, "end", text=game_id, values=(f"Missing <{el_name}> element", file))

                children = len(self.tree.get_children(command_line_folder))

                self.tree.item(command_line_folder, text=f"Invalid {el_name} Element ({children})")

    def show_help(self):

        text = """
Scans the Flashpoint platform XMLs for metadata errors. Mosty finds spelling mistakes and similar small errors.
Double click an entry to open it in Sublime Text."""

        tkinter.messagebox.showinfo("Help", text)
