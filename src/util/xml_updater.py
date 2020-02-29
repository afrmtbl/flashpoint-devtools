from lxml import etree as ET
import yaml
import uuid

from typing import Dict, Union, Tuple, Optional

aliased_keys = {
    "Extreme": "Hide",
    "Launch Command": "CommandLine",
    "Note": "Notes",
    "Languages": "Language",

    "Application Path": "ApplicationPath"
}


# XML updating exceptions
class GameNotFound(Exception):
    def __init__(self, message, game_id):
        super().__init__(message)
        self.game_id = game_id


class MissingGameId(Exception):
    def __init__(self, message, game_id):
        super().__init__(message)
        self.game_id = game_id


class MissingElement(Exception):
    def __init__(self, message, game_id, element_name):
        super().__init__(message)
        self.game_id = game_id
        self.element_name = element_name


class MissingElementValue(Exception):
    pass


# Parser exceptions
class InvalidGameId(Exception):
    pass


class ForbiddenElementChange(Exception):
    pass


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

        processed_val = None

        if isinstance(val, dict):
            prefix = f"'{key_alias}' and '{key}'" if key_alias != key else f"'{key}'"
            raise ForbiddenElementChange(f"{prefix} cannot have an object as a value")

        elif isinstance(val, list):
            processed_val = "; ".join(val)
        elif isinstance(val, bool):
            processed_val = str(val).lower()
        else:
            processed_val = str(val)

        yaml_document[key_alias] = processed_val

        if key_alias != key:
            del yaml_document[key]

    if not is_additional_application and "Additional Applications" in static_keys:
        additional_apps = yaml_document["Additional Applications"]
        for app in additional_apps:
            process_yaml(additional_apps[app], True)

    return yaml_document


def parse_changes_file(file_path: str) -> Dict:
    """Turns the user-supplied changes file into a dictionary."""

    changes = {}

    with open(file_path, "r", encoding="utf8") as changes_file:
        for index, document in enumerate(yaml.safe_load_all(changes_file.read())):
            if "GAME" not in document:
                raise InvalidGameId(f"Document {index} is missing a \'GAME\' entry")

            if "ID" in document:
                raise ForbiddenElementChange("The \'ID\' element cannot be modified")

            game_id = document["GAME"]
            del document["GAME"]
            changes[game_id] = process_yaml(document)

    return changes


try_get_ret = Union[ET.Element, Tuple[ET.Element, Optional[str]]]


def try_get_element(element_name: str, root: ET.Element, get_text: bool = False, raise_on_no_text: bool = False) -> try_get_ret:
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
                raise MissingElementValue(f"'{el.tag}' element inside '{root.tag}' is missing a value")
        else:
            return el
    else:
        raise MissingElement(f"Element '{root.tag}' is missing a '{element_name}' element", None, None)


def update_xml_element(xml_root: ET.Element, element: ET.Element, changes: dict, game_id: str, create_elements_whitelist: list, is_additional_application: bool = False):
    """
    Updates the XML tree using the data from `changes`, creating new elements if necessary."""

    # `key` being the element name
    # `value` being the text value we want to change it to
    for key, value in changes.items():
        key = aliased_keys.get(key, key)

        if key == "Additional Applications" and not is_additional_application:
            handle_additional_apps(xml_root, game_id, value, create_elements_whitelist)
            continue

        key_element = element.find(key)

        if key_element is not None:
            key_element.text = str(value)
        elif key in create_elements_whitelist:
            created_el = ET.SubElement(element, key)
            created_el.text = value
        else:
            error_text: str = f"{game_id} is missing element: \'{key}\'. If you'd prefer the element be created instead, add it on a new line in the elements whitelist (elements_whitelist.txt)"
            raise MissingElement(error_text, game_id, key)


def handle_additional_apps(xml_root: ET.Element, game_id: str, changes: dict, create_elements_whitelist: list):
    """
    Handles creating new and updating existing additional applications.

    TODO: Special handling will be included for :extras: and :message: applications.
    """

    found_apps: Dict[str, ET.Element] = {}

    for app in xml_root.iter("AdditionalApplication"):
        app_game_id = try_get_element("GameID", app, get_text=True, raise_on_no_text=True)[1]

        if app_game_id == game_id:
            app_name = try_get_element("Name", app, get_text=True, raise_on_no_text=True)[1]
            found_apps[app_name] = app

    for app_name in changes:
        if app_name in found_apps:
            changes_list = changes[app_name]
            app_element = found_apps[app_name]

            app_id = try_get_element("Id", app_element, True, True)[1]

            update_xml_element(xml_root, app_element, changes_list, app_id, create_elements_whitelist, True)
        else:
            # TODO: handle :extras: and :message:

            changes_list = changes[app_name]

            if "ApplicationPath" not in changes_list:
                raise MissingElementValue("The 'ApplicationPath' or 'Application Path' key must be included in the metadata edit in order to create a new Additional Application")
            elif "CommandLine" not in changes_list:
                raise MissingElementValue("The 'CommandLine' or 'Launch Command' key must be included in the metadata edit in order to create a new Additional Application")

            new_add_app_el = ET.SubElement(xml_root, "AdditionalApplication")

            children = {
                "Id": str(uuid.uuid4()),
                "GameID": game_id,
                "Name": app_name,

                "ApplicationPath": changes_list["ApplicationPath"],
                "CommandLine": changes_list["CommandLine"],

                "AutoRunBefore": "false",
                "WaitForExit": "false"
            }

            elements_whitelist = list(children.keys())
            update_xml_element(xml_root, new_add_app_el, children, game_id, elements_whitelist, True)
            update_xml_element(xml_root, new_add_app_el, changes_list, game_id, create_elements_whitelist, True)


def get_updated_xml(changes: dict, source_xml_path: str, create_elements_whitelist: list):
    """Wrapper function for `update_xml_element` that simplifies applying changes to an XML file."""

    parser = ET.XMLParser(remove_blank_text=True)
    tree = ET.parse(source_xml_path, parser)
    root = tree.getroot()
    # Collect game IDs that were successfully changed
    # so we can compare against the ones specified in the changes file
    results: set = set()

    for game in root.iter("Game"):
        game_id_element, game_id = try_get_element("ID", game, True, True)

        if game_id and game_id in changes:
            changes_list = changes[game_id]
            update_xml_element(root, game, changes_list, game_id, create_elements_whitelist)

            # Mark the game as successfully changed
            results.add(game_id)

    for game_id in changes:
        if game_id not in results:
            raise GameNotFound(f"Unable to find game: \'{game_id}\'", game_id)

    return tree


if __name__ == "__main__":
    from pathlib import Path
    home = str(Path.home())

    changes = parse_changes_file(f"{home}/Desktop/changes.yml")
    import json
    print(json.dumps(changes, indent=4))
    updated_xml = get_updated_xml(changes, f"{home}/Desktop/Unity.xml", ["Hide"])

    updated_xml.write("updated.xml", encoding="utf8", pretty_print=True)

    # print(ET.tostring(updated_xml.getroot(), method="xml", encoding="unicode", pretty_print=True))
