import pathlib
import sys
import unittest


SERVER_DIR = pathlib.Path(__file__).resolve().parents[1] / "server"
sys.path.insert(0, str(SERVER_DIR))

from character_set import (  # noqa: E402
    ARROW_FLAP_CHARACTER_SET,
    DEFAULT_FLAP_CHARACTER_SET,
    FIRMWARE_CHARACTER_TOKENS,
    FLAP_COUNT,
    CharacterSetError,
    display_command_for_index,
    firmware_token_for_glyph,
    prepare_display_text,
    validate_character_set,
)


class CharacterSetValidationTests(unittest.TestCase):
    def test_built_in_sequences_have_64_unique_positions(self):
        self.assertEqual(len(FIRMWARE_CHARACTER_TOKENS), FLAP_COUNT)
        self.assertEqual(len(set(FIRMWARE_CHARACTER_TOKENS)), FLAP_COUNT)
        FIRMWARE_CHARACTER_TOKENS.encode("ascii")

        for character_set in (
            DEFAULT_FLAP_CHARACTER_SET,
            ARROW_FLAP_CHARACTER_SET,
        ):
            self.assertEqual(len(character_set), FLAP_COUNT)
            self.assertEqual(validate_character_set(character_set), character_set)
            self.assertEqual(len(set(character_set)), FLAP_COUNT)

    def test_requires_exact_length_and_blank_home_position(self):
        with self.assertRaisesRegex(CharacterSetError, "exactly 64"):
            validate_character_set(DEFAULT_FLAP_CHARACTER_SET[:-1])

        invalid_home = "X" + DEFAULT_FLAP_CHARACTER_SET[1:]
        with self.assertRaisesRegex(CharacterSetError, "Character 0"):
            validate_character_set(invalid_home)

    def test_rejects_duplicate_and_control_characters(self):
        duplicate = (
            DEFAULT_FLAP_CHARACTER_SET[:-1]
            + DEFAULT_FLAP_CHARACTER_SET[-2]
        )
        with self.assertRaisesRegex(CharacterSetError, "unique"):
            validate_character_set(duplicate)

        control = (
            DEFAULT_FLAP_CHARACTER_SET[:10]
            + "\n"
            + DEFAULT_FLAP_CHARACTER_SET[11:]
        )
        with self.assertRaisesRegex(CharacterSetError, "control"):
            validate_character_set(control)


class CharacterSetMappingTests(unittest.TestCase):
    def test_standard_quote_uses_firmware_q_token(self):
        token, index = firmware_token_for_glyph(
            '"',
            DEFAULT_FLAP_CHARACTER_SET,
        )
        self.assertEqual(index, 48)
        self.assertEqual(token, "q")

    def test_arrow_reel_maps_arrows_to_their_position_tokens(self):
        up_token, up_index = firmware_token_for_glyph(
            "↑",
            ARROW_FLAP_CHARACTER_SET,
        )
        down_token, down_index = firmware_token_for_glyph(
            "↓",
            ARROW_FLAP_CHARACTER_SET,
        )

        self.assertEqual((up_index, up_token), (51, "'"))
        self.assertEqual((down_index, down_token), (56, "*"))
        self.assertEqual(
            FIRMWARE_CHARACTER_TOKENS[up_index],
            up_token,
        )

    def test_custom_reels_use_numeric_index_commands(self):
        self.assertEqual(
            display_command_for_index(0, 51, ARROW_FLAP_CHARACTER_SET),
            "m00+51",
        )
        self.assertEqual(
            display_command_for_index(5, 57, ARROW_FLAP_CHARACTER_SET),
            "m05+57",
        )
        self.assertEqual(
            display_command_for_index(5, 63, ARROW_FLAP_CHARACTER_SET),
            "m05+63",
        )

    def test_standard_reel_keeps_legacy_character_commands(self):
        self.assertEqual(
            display_command_for_index(0, 48, DEFAULT_FLAP_CHARACTER_SET),
            "m00-q",
        )
        self.assertEqual(
            display_command_for_index(5, 57, DEFAULT_FLAP_CHARACTER_SET),
            "m05-r",
        )

    def test_text_normalization_preserves_custom_glyphs_and_blanks_unknowns(self):
        result = prepare_display_text(
            'a↑↓"♥',
            ARROW_FLAP_CHARACTER_SET,
            module_count=7,
        )
        self.assertEqual(result, 'A↑↓"   ')

    def test_raw_color_codes_and_emoji_aliases_use_color_positions(self):
        raw = prepare_display_text(
            "roygbpw",
            ARROW_FLAP_CHARACTER_SET,
            module_count=7,
            raw=True,
        )
        emoji = prepare_display_text(
            "🟥🟧🟨🟩🟦🟪⬜",
            ARROW_FLAP_CHARACTER_SET,
            module_count=7,
        )
        self.assertEqual(raw, "roygbpw")
        self.assertEqual(emoji, "roygbpw")

    def test_emoji_variation_selectors_do_not_consume_flap_positions(self):
        result = prepare_display_text(
            "🟥\ufe0f🟧\ufe0f🟨\ufe0f🟩\ufe0f🟦\ufe0f🟪\ufe0f⬜\ufe0f",
            ARROW_FLAP_CHARACTER_SET,
            module_count=7,
        )
        self.assertEqual(result, "roygbpw")


if __name__ == "__main__":
    unittest.main()
