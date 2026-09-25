import unittest

from name_passcode import name_to_passcode


class NamePasscodeTests(unittest.TestCase):
    def test_name_uses_letter_positions(self):
        self.assertEqual(name_to_passcode("Ada"), "141000")

    def test_name_ignores_spaces_and_non_letters(self):
        self.assertEqual(name_to_passcode("Ava 2.0"), "121000")

    def test_blank_name_falls_back_to_default(self):
        self.assertEqual(name_to_passcode("   "), "000000")


if __name__ == "__main__":
    unittest.main()
