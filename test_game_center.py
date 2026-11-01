import importlib
import sys
import types
import unittest


class GameCenterLauncherTests(unittest.TestCase):
    def test_find_games_skips_internal_entry_files(self):
        sys.modules.pop("game_center", None)
        fake_pygame = types.ModuleType("pygame")
        sys.modules["pygame"] = fake_pygame

        module = importlib.import_module("game_center")
        scripts = [game.script_name for game in module.find_games()]

        self.assertNotIn("__init__.py", scripts)
        self.assertNotIn("__main__.py", scripts)
        self.assertEqual(scripts.count("main.py"), 1)


if __name__ == "__main__":
    unittest.main()
