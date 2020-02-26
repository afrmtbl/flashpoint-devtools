import os


class MissingElement(Exception):
    def __init__(self, message, game_id):
        super().__init__(message)
        self.game_id = game_id


class MissingElementText(Exception):
    def __init__(self, message, game_id):
        super().__init__(message)
        self.game_id = game_id


class ElementTextFailedTest(Exception):
    def __init__(self, message, game_id):
        super().__init__(message)
        self.game_id = game_id


def check_if_element_exists(xml_tree, element_name, value_test):
    root = xml_tree.getroot()

    for game in root.iter("Game"):
        game_id = game.find("ID")
        el = game.find(element_name)

        if el is not None:
            value = el.text.strip()

            if value_test:
                if value_test(value):
                    yield True
                else:
                    yield ElementTextFailedTest(f"Game with ID \"{game_id.text}\"'s <{element_name}> value failed a test", game_id.text)
            else:
                yield True
        else:
            yield MissingElement(f"Game with ID \"{game_id.text}\" is missing a <{element_name}> element", game_id.text)


def find_invalid_element_values(xml_tree, element_name, valid_values):
    root = xml_tree.getroot()

    for game in root.iter("Game"):
        game_id = game.find("ID")
        el = game.find(element_name)

        if el is not None:
            value = el.text.strip()

            if value is None:
                yield MissingElementText(f"Game with ID \"{game_id.text}\" has an empty <{element_name}> element", game_id.text)

            if value not in valid_values:
                yield game_id.text, value
        else:
            yield MissingElement(f"Game with ID \"{game_id.text}\" is missing a <{element_name}> element", game_id.text)


def find_invalid_genre_values(xml_tree):
    root = xml_tree.getroot()

    for game in root.iter("Game"):
        game_id = game.find("ID")
        genre_el = game.find("Genre")

        invalid_genres = []

        if genre_el is None:
            yield MissingElement(f"Game with ID \"{game_id.text}\" is missing a <Genre> element", game_id.text)
            continue
        else:
            if genre_el.text is None:
                yield MissingElementText(f"Game with ID \"{game_id.text}\" has an empty <Genre> element", game_id.text)
                continue

            valid_genres = ("Action", "Artillery", "Brawler", "Fighting", "First-Person Shooter", "Platformer", "Rail Shooter", "Shooter", "Vertically-Scrolling Shooter", "Adventure", "Choose Your Own Adventure", "Dating Sim", "Escape the Room", "Metroidvania", "Point and Click", "Roguelike", "RPG", "Visual Novel", "Arcade", "Breakout", "Clicker", "Dodge", "Idle", "Launch", "Pinball", "Pong", "Rhythm", "Rock-Paper-Scissors", "Runner", "Score-Attack", "Snake", "Tetris", "Variety", "Driving", "Flying", "Motocross", "Parking", "Racing", "Educational", "Math", "Quiz", "Tutorial", "Typing", "Puzzle", "Find", "Jigsaw", "Logic", "Matching", "Match-3", "Maze", "Sliding", "Sokoban", "Stealth", "Word", "Simulation", "Card", "Cooking", "Gambling", "Mahjong", "Solitaire", "Sports", "Surgery", "Tabletop", "Time Management", "Walking Simulator", "Strategy", "Lane-Based Strategy", "Node-Based Strategy", "Real-Time Strategy", "Tower Defense", "Turn-Based", "Coloring", "Dress Up", "Experimental", "Kissing", "Microsite", "Scene Creator", "Slacking", "Toy", "3D", "Adult", "Anime", "Christmas", "Community Content", "Creative", "Daily", "Fantasy", "Halloween", "Historical", "Holiday", "Horror", "Intentionally Infuriating", "Joke", "Level Editor", "Music", "Physics", "Pixel", "Politics", "Religious", "Science Fiction", "Side-Scrolling", "Space", "Story-Driven", "Western", "Zombie", "Gore", "Jumpscare", "Seizure Warning", "Sexual Content", "Strong Language", "Adventure Time", "Barbie", "Batman", "Beeserker", "Ben 10", "Cars", "Castlevania", "Cheetos", "Clifford the Big Red Dog", "Crash Bandicoot", "Curious George", "Cyberchase", "Danny Phantom", "Dexter's Laboratory", "Dinosaur Train", "Dora the Explorer", "Dragon Ball", "DragonflyTV", "Duck Hunt", "Ed, Edd n Eddy", "Fetch! with Ruff Ruffman", "Final Fantasy", "Franny's Feet", "Frozen", "Garfield", "Half-Life", "Handy Manny", "Hot Wheels", "Jimmy Neutron", "Johnny Bravo", "Jungle Junction", "Justice League", "Kirby", "Life Savers", "Little People", "Mario Bros.", "Martha Speaks", "Mega Man", "Metal Gear", "Metroid", "Mickey Mouse Clubhouse", "Minecraft", "My Little Pony", "Pac-Man", "Phineas and Ferb", "Pokemon", "Power Rangers", "Regular Show", "Samurai Jack", "Scooby-Doo", "Shaun the Sheep", "Sonic the Hedgehog", "Spider-Man", "SpongeBob SquarePants", "Spyro the Dragon", "Star Wars", "Teen Titans", "Teenage Mutant Ninja Turtles", "The Avengers", "The Legend of Zelda", "The Powerpuff Girls", "The Simpsons", "The Smurfs", "Touhou Project", "Toy Story", "Transformers", "Veggietales", "WALL-E", "WordGirl", "Wreck-It Ralph", "X-Men")

            genres = genre_el.text.strip().replace(";", ",").split(",")

            for genre in genres:
                genre = genre.strip()

                if genre and genre not in valid_genres:
                    invalid_genres.append(genre)

            if invalid_genres:
                yield game_id.text, invalid_genres


if __name__ == "__main__":

    pass

    # for file in os.listdir("C:/Users/afrm/Desktop/fps/data/games"):

        # if file.endswith(".xml"):
        #     file_path = "C:/Users/afrm/Desktop/fps/data/games/" + file

        #     xml_tree = ET.parse(file_path)

        #     for result in find_invalid_genre_values(xml_tree):
        #         if isinstance(result, Exception):
        #             print("We got an error", result)
        #         else:
        #             pass
                    # print(result)
