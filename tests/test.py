import unittest
import json
import hashlib
from lxml import etree as ET

from src.util.xml_updater import ChangesParser, XmlUpdater, explain_changes


def get_md5(input: str):
    return hashlib.md5(input.encode("utf8")).hexdigest()


class TestChangesParser(unittest.TestCase):

    def test_process_yaml_value(self):
        fn = ChangesParser.process_yaml_value

        try:
            fn({"test": 1})
        except Exception as e:
            self.assertIsInstance(e, ChangesParser.ForbiddenElementChange)

        self.assertEqual(fn(True), "true")
        self.assertEqual(fn(False), "false")

        self.assertEqual(
            fn(["en", "es", 5, True, ["nested", False]]),
            "en; es; 5; true; nested; false"
        )

        self.assertEqual(fn(3.14159), "3.14159")
        self.assertEqual(fn(692), "692")

    def test_process_yaml(self):
        fn = ChangesParser.process_yaml

        # Test to see if aliases work
        doc = {"Launch Command": 2}
        self.assertEqual(fn(doc), {"CommandLine": "2"})

        # Test aliases and list conversion
        doc = {"Release Date": "2010", "Languages": ["en", "de", "fr"]}
        self.assertEqual(fn(doc), {"ReleaseDate": "2010", "Language": "en; de; fr"})

        # Make sure elements other than "Additional Applications" cannot have objects as values
        self.assertRaises(ChangesParser.ForbiddenElementChange, fn, {"Title": {"invalid": 2}})

        doc = {"Additional Applications": {"test": 123, "Extras": {"Title": "test"}}}
        self.assertEqual(fn(doc), doc)

    def test_find_all_occurrences(self):
        fn = ChangesParser.find_all_occurrences

        query = "---\nhello blah- - --\n\n---\n--- -"
        self.assertEqual(fn("---", query), 3)
        self.assertEqual(fn("l", query), 3)

    def test_parse_changes_str(self):

        self.maxDiff = None

        jd = json.dumps
        fn = ChangesParser.parse_changes_str

        self.assertEqual(jd(fn("GAME: 1234-456-78910-78910")), '{"1234-456-78910-78910": {}}')

        big_changes = """
GAME: 562209e6-08e4-55f6-19f6-88b66d34a33f
Tags: Real-Time Strategy
Developer: Vania; SlayerSean
Version: Build 115
Release Date: 2012
Language: en
Source: www.kongregate.com
Launch Command: http://www.kongregate.com/games/SlayerSean/Overwatch.swf

Original Description: |
    An action packed RTS with singleplayer and multiplayer.

    INSTRUCTION 

    Scroll view: move mouse outside screen, or Q and E.
    Move to cover: SHIFT + click

    LAG?
    In multiplayer games make sure that nobody’s lag is in red numbers, unless you want to play a super laggy game.
    Green and yellow lag is OK.

    SHORTCUTS?
    Controls are listed in the HELP section.

---

GAME: 3a7fa2bb-ec43-4727-9bbb-c5ac1763ec3b
Tags: Platformer; Pixel

---

GAME: 21dd09da-a92f-4ead-b4fd-d68d4ecd36b6
Version: v 6.9

---

GAME: ee870760-4819-46a8-85c2-712ecd6862c7
Publisher: Armor Games
Tags: Platformer; Launch; Gore
Additional Applications:
  No Gore (Cool Math Games):
    Application Path: FPSoftware\\Flash\\flashplayer_32_sa.exe
    Launch Command: http://coolmath-games.com/0-johnny-upgrade-1/JohnnyUpgrade_Coolmath_640x480-3.swf
"""

        big_changes_result = "7d0fa6affcc2447cec1336810d2d9f40"

        # Had problems with changes that contain newlines not comparing correctly
        # so using checksum instead
        result_json_dump = jd(fn(big_changes))
        checksum = get_md5(result_json_dump)
        self.assertEqual(checksum, big_changes_result)

        changes = """
GAME: ee870760-4819-46a8-85c2-712ecd6862c7
Title: 42
---
"""
        self.assertRaises(ChangesParser.NotEnoughDocuments, fn, changes)

        changes = """
GAME:
Title: Orange
---
GAME: 22
Title: Exception
"""
        self.assertRaises(ChangesParser.InvalidGameId, fn, changes)

        changes = """
GAME: 22
GAME: 22
Title: Orange
---
Title: Exception
"""
        self.assertRaises(ChangesParser.InvalidGameId, fn, changes)

        changes = """
GAME:
ID: Orange
"""
        self.assertRaises(ChangesParser.ForbiddenElementChange, fn, changes)

        changes = """
GAME: 22
Original Description: Real
---
GAME: 22
Title: 42
"""
        self.assertRaises(ChangesParser.DuplicateGameId, fn, changes)

        changes = "GAME:e"
        self.assertRaises(ChangesParser.InvalidChangesSyntax, fn, changes)

    def test_explain_changes(self):
        pass


class TestXmlUpdater(unittest.TestCase):
    def test_try_get_element(self):
        updater = XmlUpdater()
        fn = updater.try_get_element

        root = ET.Element("Game")

        id_el = ET.SubElement(root, "ID")
        id_el.text = "test id"

        title_el = ET.SubElement(root, "Title")
        title_el.text = "test title"

        # Make sure the ID element is found
        self.assertEqual(fn("ID", root), id_el)
        # Make sure the ID element is found along with its text
        self.assertEqual(fn("ID", root, True), (id_el, "test id"))

        # Make sure MissingElement is raised when searching for a missing element
        self.assertRaises(XmlUpdater.MissingElement, fn, "invalid", root)

        # Make sure MissingElementValue is raised when getting the text of an element that does not have any
        id_el.text = None
        self.assertRaises(XmlUpdater.MissingElementValue, fn, "ID", root, True, raise_on_no_text=True)

        # Make sure MissingElementValue is not raised if raise_on_no_text is False
        self.assertEqual(fn("ID", root, True, raise_on_no_text=False), (id_el, None))

    def test_update_xml_element(self):
        updater = XmlUpdater()
        fn = updater.update_xml_element

        el = ET.Element("Game")
        desc_el = ET.SubElement(el, "Description")
        desc_el.text = "Unchanged text"

        # Make sure it doesn't let us create elements if they are not in the whitelist
        self.assertRaises(XmlUpdater.MissingElement, fn, None, el, {"Title": "Orange"}, "123-4567", [])
        self.assertRaises(XmlUpdater.MissingElement, fn, None, el, {"ID": "Orange"}, "123-4567", [])

        # Make sure we can change existing elements
        # Note: this array won't be converted to a semi-colon separated list because the changes
        # don't go through the processing step first
        fn(None, el, {"Description": [1, 2, 3, False]}, "123-4567", [])
        self.assertEqual(desc_el.text, "[1, 2, 3, False]")

        # Make sure we can create new elements from the elements whitelist
        fn(None, el, {"Description": "changed back", "Title": "Orange"}, "123-4567", ["Title"])
        self.assertEqual(desc_el.text, "changed back")
        self.assertEqual(updater.try_get_element("Title", el, True)[1], "Orange")

    def test_create_additional_application(self):
        updater = XmlUpdater()
        fn = updater.create_additional_application

        el = ET.Element("LaunchBox")

        app = fn(el, "123-4567", "Test Application", "test path", "test commandline")

        self.assertIsInstance(app, ET._Element)

        # Make sure the additional application has all the required elements
        self.assertIsInstance(updater.try_get_element("Id", app, True, True)[0], ET._Element)
        self.assertIsInstance(updater.try_get_element("GameID", app, True, True)[0], ET._Element)
        self.assertIsInstance(updater.try_get_element("Name", app, True, True)[0], ET._Element)
        self.assertIsInstance(updater.try_get_element("ApplicationPath", app, True, True)[0], ET._Element)
        self.assertIsInstance(updater.try_get_element("CommandLine", app, True, True)[0], ET._Element)
        self.assertIsInstance(updater.try_get_element("AutoRunBefore", app, True, True)[0], ET._Element)
        self.assertIsInstance(updater.try_get_element("WaitForExit", app, True, True)[0], ET._Element)

    def test_handle_additional_apps(self):
        updater = XmlUpdater()
        fn = updater.handle_additional_apps

        parser = ET.XMLParser(remove_blank_text=True)
        tree = ET.parse("tests/sample_xml.xml", parser)
        root = tree.getroot()

        changes = {
            "Message": {
                "CommandLine": "test commandline",
                "WaitForExit": "true",
                "AutoRunBefore": "true"
            },
            "Extras": "Changed commandline using string instead of dict",

            "беларуская мова": {
                "CommandLine": "http://phet.colorado.edu/sims/collision-lab/collision-lab_be.html",
                "ApplicationPath": "FPSoftware\\Flash\\flashplayer_32_sa.exe"
            }
        }

        changes_2 = {
            "Extras": "Created a new extra with a string",
            "Message": {
                "ApplicationPath": "flash.exe",
                "CommandLine": ":message: test",
                "Name": "Created a new message with a dict",
                "WaitForExit": "test wait",
                "Orange": "Testing element whitelist",
                "Id": "static uuid message"
            }
        }

        changes_fix_hash = {
            "беларуская мова": {
                "Id": "static uuid russia"
            }
        }

        changes_2_fix_hash = {
            "Extras": {
                "Id": "static uuid id"
            }
        }

        fn(root, "d3d2fa4d-31d3-ee55-0df6-922f76c6efc0", changes, [])
        fn(root, "9aeb262e-5a55-48a4-8eb1-265925880b90", changes_2, ["Orange"])

        fn(root, "d3d2fa4d-31d3-ee55-0df6-922f76c6efc0", changes_fix_hash, [])
        fn(root, "9aeb262e-5a55-48a4-8eb1-265925880b90", changes_2_fix_hash, [])

        self.assertRaises(XmlUpdater.MissingElement, fn, root, "9aeb262e-5a55-48a4-8eb1-265925880b90", changes_2, [])
        self.assertRaises(XmlUpdater.ForbiddenElementChange, fn, root, "9aeb262e-5a55-48a4-8eb1-265925880b90", {"Invalid": "cant set str"}, [])

        missing_app_path = {"Invalid": {}}
        missing_command_line = {"Invalid": {"ApplicationPath": "dsa"}}
        self.assertRaises(XmlUpdater.MissingElementValue, fn, root, "9aeb262e-5a55-48a4-8eb1-265925880b90", missing_app_path, [])
        self.assertRaises(XmlUpdater.MissingElementValue, fn, root, "9aeb262e-5a55-48a4-8eb1-265925880b90", missing_command_line, [])

        xml_str = ET.tostring(tree.getroot(), method="xml", encoding="unicode", pretty_print=True)
        checksum = get_md5(xml_str)

        self.assertEqual(checksum, "80c61a20ca2d1456f925505423337fe7")

    def test_get_updated_xml(self):
        updater = XmlUpdater()
        fn = updater.get_updated_xml

        # Test modifying existing games
        changes = ChangesParser.parse_changes_str("""
GAME: 25a91b3a-a9e1-db58-9e97-75c33bbe25fa
Title: Changed Title
Series: New Series
Genre:
  - Coloring
  - RPG
  - Text Adventure
PlayCount: 17
Notes: no notes

---

GAME: 9aeb262e-5a55-48a4-8eb1-265925880b90
Title: Rush Hour 2
Platform: Flash
Source: youtube.com
Genre: [Driving, Coloring, Action, RPG]
Developer: develops
Hide: Yes
Publisher: new

---

GAME: d3d2fa4d-31d3-ee55-0df6-922f76c6efc0
Broken: Yes
NewElement: test
""")

        updated_xml, games_changed, games_failed = fn(changes, "tests/sample_xml.xml", ["NewElement"])

        self.assertEqual(games_changed, {"d3d2fa4d-31d3-ee55-0df6-922f76c6efc0", "9aeb262e-5a55-48a4-8eb1-265925880b90", "25a91b3a-a9e1-db58-9e97-75c33bbe25fa"})
        self.assertEqual(len(games_failed), 0)

        # Make sure creating new elements fail if not in whitelist
        changes = ChangesParser.parse_changes_str("""
GAME: 9aeb262e-5a55-48a4-8eb1-265925880b90
NewElement: 123

---

GAME: ba3d2d72-6192-2925-3bae-2db312ffd4a8
Additional Applications:
  Message: hello!
""")

        updated_xml, games_changed, games_failed = fn(changes, "tests/sample_xml.xml", [])
        self.assertIn("ba3d2d72-6192-2925-3bae-2db312ffd4a8", games_changed)
        self.assertIn("9aeb262e-5a55-48a4-8eb1-265925880b90", games_failed)
        self.assertIsInstance(games_failed["9aeb262e-5a55-48a4-8eb1-265925880b90"], XmlUpdater.MissingElement)


if __name__ == "__main__":
    unittest.main()
