import xml.etree.ElementTree as ET
import yaml
import json

from typing import Dict

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


def parse_changes_file(file_path: str):
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


def get_updated_xml(changes, source_xml_path: str, create_elements_whitelist: list):
    """Updates an ElementTree based on the changes provided"""

    tree = ET.parse(source_xml_path)
    root = tree.getroot()
    # Collect game IDs that were sucessfully changed
    # so we can compare against the ones specified in the changes file
    results: set = set()

    for game in root.iter("Game"):
        id_element = game.find("ID")

        if id_element is None:
            raise MissingGameId("ID element is missing", None)

        game_id = id_element.text

        if game_id in changes:
            changes_list = changes[game_id]
            # `key` being the element name
            # `value` being the text value we want to change it to
            for key, value in changes_list.items():
                key = aliased_keys.get(key, key)
                print(key)
                key_element = game.find(key)

                if key_element is not None:
                    key_element.text = str(value)
                elif key in create_elements_whitelist:
                    created_el = ET.SubElement(game, key)
                    created_el.text = value
                else:
                    error_text: str = f"{game_id} is missing element: \'{key}\'. If you'd prefer the element be created instead, add it on a new line in the elements whitelist (elements_whitelist.txt)"
                    raise MissingElement(error_text, game_id, key)

            # Mark the game as sucessfully changed
            results.add(game_id)

    for game_id in changes:
        if game_id not in results:
            raise GameNotFound(f"Unable to find game: \'{game_id}\'", game_id)

    return tree


if __name__ == "__main__":
    from pathlib import Path
    home = str(Path.home())

    changes = parse_changes_file(f"{home}/Desktop/changes.yml")
    print(json.dumps(changes, indent=4))
    updated_xml = get_updated_xml(changes, f"{home}/Desktop/Unity.xml", [])

    updated_xml.write("updated.xml", encoding="utf8")

    # print(ET.tostring(updated_xml.getroot(), method="xml", encoding="unicode"))
