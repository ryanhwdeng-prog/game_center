import json
import tempfile
import unittest
from pathlib import Path

from guess_my_password.password_logic import (
    CHEAT_PASSWORD,
    DEFAULT_PASSWORD,
    DEFAULT_TITLE,
    GamePasswordState,
    load_state,
)


class PasswordGameTests(unittest.TestCase):
    def test_default_state_is_seeded(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            state_path = Path(tmp_dir) / "state.json"
            state = load_state(state_path)

            self.assertEqual(state.password, DEFAULT_PASSWORD)
            self.assertEqual(state.title, DEFAULT_TITLE)

    def test_correct_password_allows_new_password_and_title_to_be_saved(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            state_path = Path(tmp_dir) / "state.json"
            state = GamePasswordState(path=state_path)
            state.set_password("0000", new_password="9876", new_title="My New Game")

            saved = load_state(state_path)
            self.assertEqual(saved.password, "9876")
            self.assertEqual(saved.title, "My New Game")

    def test_cheat_password_is_accepted_and_cannot_be_saved_as_the_real_password(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            state_path = Path(tmp_dir) / "state.json"
            state = GamePasswordState(path=state_path)
            ok = state.set_password("0000", new_password=CHEAT_PASSWORD, new_title="Cheat Title")

            self.assertFalse(ok)
            saved = load_state(state_path)
            self.assertEqual(saved.password, DEFAULT_PASSWORD)
            self.assertEqual(saved.title, DEFAULT_TITLE)

    def test_cheat_password_works_like_a_valid_guess_but_does_not_replace_the_real_password(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            state_path = Path(tmp_dir) / "state.json"
            state = GamePasswordState(path=state_path)
            state.set_password("0000", new_password="2468", new_title="Second Name")

            ok = state.set_password(CHEAT_PASSWORD, new_password="1357", new_title="Secret Rename")

            self.assertTrue(ok)
            saved = load_state(state_path)
            self.assertEqual(saved.password, "1357")
            self.assertEqual(saved.title, "Secret Rename")
            self.assertEqual(json.loads(state_path.read_text(encoding="utf-8"))["password"], "1357")


if __name__ == "__main__":
    unittest.main()
