from tkinter import *
import tkinter.ttk as ttk

from tkinter.filedialog import askopenfilename

import xml.etree.ElementTree as ET
import requests
import threading


class MissingFilesTab(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=10)
        self.columnconfigure(2, weight=1)

        self.add_widgets()

    def add_widgets(self):
        description = ttk.Label(self, text="Find files in the XML that can't be found on a hosted Flashpoint copy", style="MY.TLabel")
        description.grid(columnspan=3, sticky="W", pady=(5, 10))

        ttk.Label(self, text="XML File", style="MY.TLabel").grid(row=1, column=0)
        ttk.Label(self, text="Server URL", style="MY.TLabel").grid(row=2, column=0)

        self.xml_path = ttk.Entry(self)
        self.xml_path.grid(row=1, column=1, sticky=EW, pady=(5, 5))

        ttk.Button(self, text="Browse", command=self.choose_xml_file).grid(row=1, column=2, sticky=E)

        self.server_url = ttk.Entry(self)
        self.server_url.insert(0, "https://unstable.life")
        self.server_url.grid(row=2, column=1, sticky=EW, pady=(5, 5))

        def reset_server_url():
            self.server_url.delete(0, END)
            self.server_url.insert(0, "https://unstable.life")

        default_server_button = ttk.Button(self, text="Default", command=reset_server_url)
        default_server_button.grid(row=2, column=2, sticky=E)

        search_button = ttk.Button(self, text="Search", command=self.threaded_verify)
        search_button.grid(row=3, columnspan=3, sticky=E, pady=20)

    def choose_xml_file(self):
        file = askopenfilename(filetypes=[("XML File", "*.xml")])
        self.xml_path.delete(0, END)
        self.xml_path.insert(0, file)

    def verify_xml(self, xml_path, server_url):
        tree = ET.parse(xml_path)
        root = tree.getroot()

        session = requests.Session()

        reqs = 0

        for game in root.findall("Game"):
            app_path = game.find("ApplicationPath").text.replace("\\", "/")
            command_path = game.find("CommandLine").text.split("://")[-1]

            final_app_url = f"{server_url}/Flashpoint/{app_path}"
            final_command_url = f"{server_url}/Flashpoint/Server/htdocs/{command_path}"

            with session.get(final_app_url) as response:
                if not response.ok:
                    print(f"App bad: {final_app_url}")
                else:
                    print(f"App good: {final_app_url}")

            with session.get(final_command_url) as response:
                if not response.ok:
                    print(f"Command bad: {final_command_url}")
                else:
                    print(f"Command good: {final_command_url}")

            reqs += 1
            if reqs > 10:
                break

        print("Finished search")

    def threaded_verify(self):
        thread = threading.Thread(
            target=self.verify_xml,
            args=(
                self.xml_path.get(),
                self.server_url.get()
            )
        )
        thread.start()
