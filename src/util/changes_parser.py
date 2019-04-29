import xml.etree.ElementTree as ET

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

	def parse_changes_file(file_path):
		with open(file_path, "r", encoding="utf-8") as file:
			current_game = None
			changes = {}

			for line in file:
				line = line.strip()

				if line[0:4] == "GAME":
					current_game = line.split(" ", maxsplit=1)[1]
					changes[current_game] = []
				elif ":" in line:
					key, value = line.split(":", maxsplit=1)

					key = key.strip()
					value = value.strip()

					changes[current_game].append((key, value))
			return changes

	def get_updated_xml(changes, source_xml_path):
		tree = ET.parse(source_xml_path)
		root = tree.getroot()

		results = set()

		for game in root.iter("Game"):
			id_element = game.find("ID")
			game_id = id_element.text

			if game_id in changes:
				changes_list = changes[game_id]

				for key, value in changes_list:
					key_element = game.find(key)

					if key_element != None:
						key_element.text = value
					else:
						raise ChangesParser.MissingElement(f"{game_id} is missing element: {key}", game_id, key)
			results.add(game_id)

		for game_id in changes:
			if game_id not in results:
				raise ChangesParser.GameNotFound(f"Unable to find game: {game_id}", game_id)

		return tree

if __name__ == '__main__':
	changes = ChangesParser.parse_changes_file("C:/Users/afrm/Desktop/changes.txt")
	ChangesParser.get_updated_xml(changes, "C:/Users/afrm/Desktop/Flash.xml")
