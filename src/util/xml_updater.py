"""Handles parsing the YAML changes files and actually applying the changes to an XML file."""

from lxml import etree as ET
import yaml
import uuid

import re

from typing import Dict, Union, Tuple, Optional, List

aliased_keys = {
    "Application Path": "ApplicationPath",
    "Launch Command": "CommandLine",
    "Command Line": "CommandLine",

    "Extreme": "Hide",
    "Note": "Notes",
    "Languages": "Language",
    "Release Date": "ReleaseDate",
    "Alternate Titles": "AlternateTitles",
    "Play Mode": "PlayMode",
    "Original Description": "OriginalDescription"
}


class ChangesParser:

    class InvalidGameId(Exception):
        pass

    class ForbiddenElementChange(Exception):
        pass

    class NotEnoughDocuments(Exception):
        pass

    class DuplicateGameId(Exception):
        pass

    @staticmethod
    def process_yaml_value(value):
        processed_val = None

        if isinstance(value, dict):
            raise ChangesParser.ForbiddenElementChange()

        elif isinstance(value, list):
            processed_val = "; ".join([ChangesParser.process_yaml_value(el) for el in value])
        elif isinstance(value, bool):
            processed_val = str(value).lower()
        else:
            processed_val = str(value)

        return processed_val

    @staticmethod
    def process_yaml(yaml_document: Dict, is_additional_application: bool = False):
        """
        A post-processing operation on the YAML data to be used before putting
        it into the XML.

        Converts key names into their corresponding alias names, transforms YAML
        values into a format the Flashpoint XML understands, transforms lists into
        a semicolon-separated string, and lowercases `True` and `False`.
        """

        static_keys = list(yaml_document.keys())

        for key in static_keys:

            if not is_additional_application and key == "Additional Applications":
                continue

            key_alias = aliased_keys.get(key, key)
            val = yaml_document[key]

            try:
                yaml_document[key_alias] = ChangesParser.process_yaml_value(val)
            except ChangesParser.ForbiddenElementChange:
                prefix = f"'{key_alias}' and '{key}'" if key_alias != key else f"'{key}'"
                raise ChangesParser.ForbiddenElementChange(f"{prefix} cannot have an object as a value")

            if key_alias != key:
                del yaml_document[key]

        if not is_additional_application and "Additional Applications" in static_keys:
            additional_apps = yaml_document["Additional Applications"]
            for app in additional_apps:
                app_val = additional_apps[app]

                if isinstance(app_val, dict):
                    ChangesParser.process_yaml(additional_apps[app], True)
                else:
                    additional_apps[app] = ChangesParser.process_yaml_value(app_val)

        return yaml_document

    @staticmethod
    def find_all_occurrences(query, string) -> int:
        return len(re.findall(query, string, flags=re.MULTILINE))

    @staticmethod
    def parse_changes_file(file_path: str) -> Dict:
        """Turns the user-supplied changes file into a dictionary."""

        changes: Dict[str, dict] = {}

        with open(file_path, "r", encoding="utf8") as changes_file:
            changes_str = changes_file.read()

            game_id_count = ChangesParser.find_all_occurrences("^GAME:", changes_str)
            new_document_count = ChangesParser.find_all_occurrences("^---", changes_str)

            if new_document_count != game_id_count - 1:
                raise ChangesParser.NotEnoughDocuments("Each new game, except for the last, should be followed by three dashes (---). The first game should not be preceded by three dashes.")

            for index, document in enumerate(yaml.safe_load_all(changes_str)):
                if not document or "GAME" not in document:
                    raise ChangesParser.InvalidGameId(f"Document {index + 1} is missing a \'GAME\' entry")

                if "ID" in document:
                    raise ChangesParser.ForbiddenElementChange("The \'ID\' element cannot be modified")

                game_id = document["GAME"]

                if game_id in changes:
                    raise ChangesParser.DuplicateGameId(f"The game ID \'{game_id}\' already has changes associated with it")

                del document["GAME"]
                changes[game_id] = ChangesParser.process_yaml(document)

        return changes


try_get_ret = Union[ET.Element, Tuple[ET.Element, Optional[str]]]


class XmlUpdater:

    class GameNotFound(Exception):
        def __init__(self, message, game_id):
            super().__init__(message)
            self.game_id = game_id

    class MissingElement(Exception):
        def __init__(self, message, game_id, element_name):
            super().__init__(message)
            self.game_id = game_id
            self.element_name = element_name

    class MissingElementValue(Exception):
        def __init__(self, message, game_id, element_name):
            super().__init__(message)
            self.game_id = game_id
            self.element_name = element_name

    class ForbiddenElementChange(Exception):
        def __init__(self, message, game_id, element_name):
            super().__init__(message)
            self.game_id = game_id
            self.element_name = element_name

    def __init__(self):
        self.current_game_id: Optional[str] = None

    def try_get_element(self, element_name: str, root: ET.Element, get_text: bool = False, raise_on_no_text: bool = False) -> try_get_ret:
        """
        Tries to retrieve an `element_name` child inside of `root` and returns the element and
        optionally its text if successful.
        """

        el = root.find(element_name)

        if el is not None:
            if get_text:
                el_text = el.text

                if el_text or not raise_on_no_text:
                    return el, el_text
                else:
                    raise self.MissingElementValue(f"'{el.tag}' element inside '{root.tag}' is missing a value", self.current_game_id, element_name)
            else:
                return el
        else:
            raise self.MissingElement(f"Element '{root.tag}' is missing a '{element_name}' element", self.current_game_id, element_name)

    def update_xml_element(self, xml_root: ET.Element, element: ET.Element, changes: dict, game_id: str, create_elements_whitelist: list, is_additional_application: bool = False):
        """
        Updates the XML tree using the data from `changes`, creating new elements if necessary.
        """

        # `key` being the element name
        # `value` being the text value we want to change it to
        for key, value in changes.items():
            key = aliased_keys.get(key, key)

            if key == "Additional Applications" and not is_additional_application:
                self.handle_additional_apps(xml_root, game_id, value, create_elements_whitelist)
                continue

            key_element = element.find(key)

            if key_element is not None:
                key_element.text = str(value)
            elif key in create_elements_whitelist:
                created_el = ET.SubElement(element, key)
                created_el.text = value
            else:
                error_text: str = f"{game_id} is missing element: \'{key}\'. If you'd prefer the element be created instead, add it on a new line in the elements whitelist (elements_whitelist.txt)"
                raise self.MissingElement(error_text, game_id, key)

    def create_additional_application(self, xml_root: ET.Element, game_id: str, app_name: str, application_path: str, command_line: str) -> ET.Element:
        new_add_app_el = ET.SubElement(xml_root, "AdditionalApplication")

        children = {
            "Id": str(uuid.uuid4()),
            "GameID": game_id,
            "Name": app_name,

            "ApplicationPath": application_path,
            "CommandLine": command_line,

            "AutoRunBefore": "false",
            "WaitForExit": "false"
        }

        elements_whitelist = list(children.keys())
        self.update_xml_element(xml_root, new_add_app_el, children, game_id, elements_whitelist, True)

        return new_add_app_el

    def handle_additional_apps(self, xml_root: ET.Element, game_id: str, changes: dict, create_elements_whitelist: list):
        """Handles creating new and updating existing additional applications."""

        found_apps: Dict[str, ET.Element] = {}

        for app in xml_root.iter("AdditionalApplication"):

            app_game_id = self.try_get_element("GameID", app, get_text=True, raise_on_no_text=True)[1]

            if app_game_id == game_id:
                app_name = self.try_get_element("Name", app, get_text=True, raise_on_no_text=True)[1]
                found_apps[app_name] = app

        for app_name in changes:
            # If the additional application already exists
            if app_name in found_apps:
                changes_list = changes[app_name]
                app_element = found_apps[app_name]

                app_id = self.try_get_element("Id", app_element, True, True)[1]

                if isinstance(changes_list, dict):
                    self.update_xml_element(xml_root, app_element, changes_list, app_id, create_elements_whitelist, True)
                elif isinstance(changes_list, str) and (app_name == "Extras" or app_name == "Message"):
                    changes_list = {"CommandLine": changes_list}
                    self.update_xml_element(xml_root, app_element, changes_list, app_id, create_elements_whitelist, True)
                else:
                    msg = f"Inside of the 'Additional Applications' key, only 'Extras' and 'Message' can have a string as a value"
                    raise self.ForbiddenElementChange(msg, self.current_game_id, None)

            else:
                # In the case of `Extras: str` and `Message: str`, this will be a string
                changes_list = changes[app_name]

                if isinstance(changes_list, dict):
                    if "ApplicationPath" not in changes_list:
                        msg = f"{app_name}: The 'ApplicationPath' or 'Application Path' key must be included in the metadata edit in order to create a new Additional Application"
                        raise self.MissingElementValue(msg, self.current_game_id, "ApplicationPath")
                    elif "CommandLine" not in changes_list:
                        msg = f"{app_name}: The 'CommandLine' or 'Launch Command' key must be included in the metadata edit in order to create a new Additional Application"
                        raise self.MissingElementValue(msg, self.current_game_id, "CommandLine")

                    application_path = changes_list["ApplicationPath"]
                    command_line = changes_list["CommandLine"]

                    new_add_app_el = self.create_additional_application(xml_root, game_id, app_name, application_path, command_line)
                    self.update_xml_element(xml_root, new_add_app_el, changes_list, game_id, create_elements_whitelist, True)

                elif isinstance(changes_list, str) and (app_name == "Extras" or app_name == "Message"):
                    application_path = ":extras:" if app_name == "Extras" else ":message:"
                    new_add_app_el = self.create_additional_application(xml_root, game_id, app_name, application_path, changes_list)
                else:
                    msg = f"Inside of the 'Additional Applications' key, only 'Extras' and 'Message' can have a string as a value.\nIf you're trying to create an alternate, the value must be a mapping."
                    raise self.ForbiddenElementChange(msg, self.current_game_id, None)

    def get_updated_xml(self, changes: dict, source_xml_path: str, create_elements_whitelist: list) -> Tuple[ET.Element, set, list]:
        """Wrapper function for `update_xml_element` that simplifies applying changes to an XML file."""

        parser = ET.XMLParser(remove_blank_text=True)
        tree = ET.parse(source_xml_path, parser)
        root = tree.getroot()
        # Collect game IDs that were successfully changed
        # so we can compare against the ones specified in the changes file
        games_changed: set = set()
        games_failed: List[Exception] = []

        for game in root.iter("Game"):
            game_id_element, game_id = self.try_get_element("ID", game, True, True)

            if game_id and game_id in changes:
                changes_list = changes[game_id]
                self.current_game_id = game_id
                try:
                    self.update_xml_element(root, game, changes_list, game_id, create_elements_whitelist)
                    games_changed.add(game_id)
                except Exception as e:
                    games_failed.append(e)

        return tree, games_changed, games_failed


def explain_changes(all_changes: dict, is_additional_application: bool = False) -> str:
    explanation = ""
    spacing = "      "

    def changes_to_str(changes: dict, is_additional_application: bool = False):
        explanation = ""
        for element_name in changes:

            val = changes[element_name]

            if element_name == "Additional Applications" and not is_additional_application:
                for app_name in val:
                    app_changes = val[app_name]

                    if isinstance(app_changes, str):
                        line = f"Additional application \"{app_name}\" (created or modified)\n"
                        line += (spacing * 2) + f"\"CommandLine\" element now has a value of \"{app_changes}\"\n"
                        explanation += "\n" + spacing + line
                    elif isinstance(app_changes, dict):
                        line = f"Additional application \"{app_name}\" (created or modified)\n"
                        line += changes_to_str(app_changes, is_additional_application=True)
                        explanation += "\n" + spacing + line
                    else:
                        raise Exception(f"Invalid additional application value ({app_name}, {app_changes})")
            else:
                line = f"\"{element_name}\" element was changed to \"{val}\"\n"
                cur_spacing = 2 * spacing if is_additional_application else spacing
                suffix = "" if is_additional_application else "\n"
                explanation += suffix + cur_spacing + line

        return explanation

    for game_id in all_changes:
        explanation += game_id + "\n"
        game_changes = all_changes[game_id]

        explanation += changes_to_str(game_changes)

        explanation += "\n"

    return explanation


if __name__ == "__main__":
    from pathlib import Path
    home = str(Path.home())

    changes = ChangesParser.parse_changes_file(f"{home}/Desktop/changes.yml")
    exp = explain_changes(changes)

    print(changes)

    # print(exp)
    # import json
    # print(json.dumps(changes, indent=4))
    # updater = XmlUpdater()

    # updated_xml, games_changed, games_failed = updater.get_updated_xml(changes, f"{home}/Desktop/platform_xmls/Flash.xml", ["Tags", "OriginalDescription", "ReleaseDate"])
    # print(games_changed)

    # print(games_failed)

    # print(changed_games)

    # updated_xml.write("updated.xml", encoding="utf8", pretty_print=True)

    # print(ET.tostring(updated_xml.getroot(), method="xml", encoding="unicode", pretty_print=True))
