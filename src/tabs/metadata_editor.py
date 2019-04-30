import tkinter as tk
import tkinter.ttk as ttk

from tkinter.filedialog import askopenfilename, asksaveasfile
import tkinter.messagebox

import threading
import os

from ..util.changes_parser import ChangesParser


class MetadataEditorTab(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.generating_xml = False

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=10)
        self.columnconfigure(2, weight=1)

        self.add_widgets()

    def add_widgets(self):
        description = ttk.Label(self, text="Quickly edit metadata from the specified XML file using a list of changes", style="MY.TLabel")
        description.grid(columnspan=3, sticky="W", pady=(5, 10))

        ttk.Label(self, text="XML File", style="MY.TLabel").grid(row=1, column=0)

        self.xml_path = ttk.Entry(self)
        self.xml_path.grid(row=1, column=1, sticky=tk.EW, pady=(5, 5))

        ttk.Button(self, text="Browse", command=self.choose_xml_file).grid(row=1, column=2, sticky=tk.E)

        ttk.Label(self, text="Changes File", style="MY.TLabel").grid(row=2, column=0)
        self.change_file_path = ttk.Entry(self)
        self.change_file_path.grid(row=2, column=1, sticky=tk.EW, pady=(5, 5))

        self.browse_changes_button = ttk.Button(self, text="Browse", command=self.choose_changes_file)
        self.browse_changes_button.grid(row=2, column=2, sticky=tk.E)

        self.help_button = ttk.Button(self, text="Help", command=self.show_help)
        self.help_button.grid(row=4, column=1, sticky=tk.E, pady=20)

        self.generate_button = ttk.Button(self, text="Generate XML", command=self.threaded_update)
        self.generate_button.grid(row=4, column=2, sticky=tk.E, pady=20)

    def choose_xml_file(self):
        file = askopenfilename(filetypes=[("XML File", "*.xml")])
        self.xml_path.delete(0, tk.END)
        self.xml_path.insert(0, file)

    def choose_changes_file(self):
        file = askopenfilename()
        self.change_file_path.delete(0, tk.END)
        self.change_file_path.insert(0, file)

    def update_metadata(self, xml_file_path, changes_file_path):
        if not os.path.isfile(xml_file_path):
            tkinter.messagebox.showerror("File not found", f"Invalid file path: \'{xml_file_path}\'")
            self.generating_xml = False
            return

        if not os.path.isfile(changes_file_path):
            tkinter.messagebox.showerror("File not found", f"Invalid file path: \'{changes_file_path}\'")
            self.generating_xml = False
            return

        self.generating_xml = True
        self.generate_button.configure(state=tk.DISABLED)

        try:
            changes = ChangesParser.parse_changes_file(changes_file_path)
            updated_xml = ChangesParser.get_updated_xml(changes, xml_file_path)

            ftypes = [("XML File", "*.xml")]
            save_file = asksaveasfile(mode="wb", defaultextension=".xml", initialfile="updated", filetypes=ftypes)
            if save_file:
                updated_xml.write(save_file, encoding="utf-8")

        except ChangesParser.GameNotFound as e:
            tkinter.messagebox.showerror("Unable to find game", f"The following game ID was specified in the changes file, but couldn\'t be found in the XML:\n\n{e.game_id}")
        except ChangesParser.MissingElement as e:
            tkinter.messagebox.showerror("Unable to find element", f"Game with ID \'{e.game_id}\' is missing the \'{e.element_name}\' element")
        except ChangesParser.InvalidElementName as e:
            tkinter.messagebox.showerror("Invalid element name", str(e))
        except ChangesParser.NoCurrentGame as e:
            tkinter.messagebox.showerror("No game specified", str(e))
        finally:
            self.generating_xml = False
            self.generate_button.configure(state=tk.NORMAL)

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

GAME $GAME_ID
$ELEMENT_NAME: New Value

For example:
GAME dbde64aa-fbd7-4837-bba5-63d923092486
    Title: Swag
    Genre: Adventure, Point'n'Click
    Publisher: Newgrounds.com
GAME ea84e831-ee4f-44ec-b769-b657c8ffa8e3
    Genre: Puzzle, Tetris, Physics

Any leading and trailing whitespace is automatically stripped, so it can be used to increase readability"""

        tkinter.messagebox.showinfo("Help", text)
