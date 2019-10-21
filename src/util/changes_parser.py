import xml.etree.ElementTree as ET

from typing import Dict, Tuple

ChangeGroup = Tuple[str, str]
XMLChanges = Dict[str, ChangeGroup]

aliased_keys = {
    "Extreme": "Hide",
    "Launch Command": "CommandLine",
    "Note": "Notes"
}


class ChangesParser:
    class GameNotFound(Exception):
        def __init__(self, message, game_id):
            super().__init__(message)
            self.game_id = game_id

    class MissingElement(Exception):
        def __init__(self, message, game_id, element_name):
            super().__init__(message)
            self.game_id = game_id
            self.element_name = element_name

    class NoCurrentGame(Exception):
        pass

    class InvalidElementName(Exception):
        pass

    """Creates a dictionary of changes specified by the changes file"""
    @staticmethod
    def parse_changes_file(file_path: str) -> XMLChanges:
        with open(file_path, "r", encoding="utf-8") as file:
            current_game = None
            # changes are stored as:
            # $game_id: [($element_name, $new_text_value)]
            changes: dict = {}

            for index, line in enumerate(file):
                # get rid of all extra whitespace
                line = line.strip()

                # if we're at the start of a new game
                if line[0:4] == "GAME":
                    current_game = line.split(" ", maxsplit=1)[1]
                    changes[current_game] = []
                # if were at the start of a property for the current game
                elif ":" in line:
                    if current_game:
                        key, value = line.split(":", maxsplit=1)

                        if not key.strip():
                            error_text = f"An element name must precede a \':\' (line {index + 1})"
                            raise ChangesParser.InvalidElementName(error_text)

                        key = key.strip()
                        value = value.strip()

                        if key in aliased_keys:
                            key = aliased_keys[key]

                        changes[current_game].append((key, value))
                    else:
                        error_text = f"A game ID must come before changes to properties (line {index + 1})"
                        raise ChangesParser.NoCurrentGame(error_text)
            return changes

    """Updates an ElementTree based on the changes provided"""
    @staticmethod
    def get_updated_xml(changes: XMLChanges, source_xml_path: str, create_elements_whitelist: list):
        tree = ET.parse(source_xml_path)
        root = tree.getroot()
        # collect game IDs that were sucessfully changed
        # so we can compare against the ones specified in the changes file
        results: set = set()

        for game in root.iter("Game"):
            id_element = game.find("ID")
            game_id: str = id_element.text

            if game_id in changes:
                changes_list: ChangeGroup = changes[game_id]
                # key being the element name
                # value being the text value we want to change it to
                for key, value in changes_list:
                    key_element = game.find(key)

                    if key_element is not None:
                        key_element.text = value
                    elif key in create_elements_whitelist:
                        created_el = ET.SubElement(game, key)
                        created_el.text = value
                    else:
                        error_text: str = f"{game_id} is missing element: \'{key}\'. If you'd prefer the element be created instead, add it on a new line in the elements whitelist (elements_whitelist.txt)"
                        raise ChangesParser.MissingElement(error_text, game_id, key)
            # mark the game as sucessfully changed
            results.add(game_id)

        for game_id in changes:
            if game_id not in results:
                raise ChangesParser.GameNotFound(f"Unable to find game: \'{game_id}\'", game_id)

        return tree


# quick test code
if __name__ == '__main__':
    from pathlib import Path
    home = str(Path.home())

    changes = ChangesParser.parse_changes_file(f"{home}/Desktop/changes.txt")
    updated_xml = ChangesParser.get_updated_xml(changes, f"{home}/Desktop/Flash.xml", [])

    # updated_xml.write("updated.xml", encoding="utf8")

    print(ET.tostring(updated_xml.getroot(), method="xml", encoding="unicode"))
