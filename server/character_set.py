"""Physical flap character-set validation and firmware position mapping.

The module firmware accepts a fixed set of one-byte command tokens. Those
tokens identify reel positions; they do not have to match the glyph printed on
the flap at that position. Keeping the two sequences separate lets Splitflap OS
support custom physical reels without requiring custom firmware.
"""

import unicodedata


FLAP_COUNT = 64

# Fixed one-byte tokens understood by the original and universal firmware.
FIRMWARE_CHARACTER_TOKENS = (
    " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$&()-+=;q:%'.,/?*roygbpw"
)

# Physical glyphs used by the standard Adam G Makes reel. The quote glyph at
# index 48 is addressed by the firmware token ``q``.
DEFAULT_FLAP_CHARACTER_SET = (
    " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$&()-+=;\":%'.,/?*roygbpw"
)

# Common alternate reel: up/down arrows replace apostrophe/asterisk at the
# same physical positions.
ARROW_FLAP_CHARACTER_SET = (
    " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$&()-+=;\":%↑.,/?↓roygbpw"
)

CHARACTER_SET_PRESETS = {
    "standard": {
        "name": "Standard reel",
        "characters": DEFAULT_FLAP_CHARACTER_SET,
    },
    "arrows": {
        "name": "Arrow reel (↑ / ↓)",
        "characters": ARROW_FLAP_CHARACTER_SET,
    },
}

COLOR_ALIASES = {
    "\U0001f7e5": "r",
    "\U0001f7e7": "o",
    "\U0001f7e8": "y",
    "\U0001f7e9": "g",
    "\U0001f7e6": "b",
    "\U0001f7ea": "p",
    "\u2b1c": "w",
    "\u2b1b": " ",
}

EMOJI_VARIATION_SELECTORS = ("\ufe0e", "\ufe0f")


class CharacterSetError(ValueError):
    """Raised when a physical flap character sequence is not usable."""


def validate_character_set(value):
    """Return a valid 64-glyph sequence or raise ``CharacterSetError``.

    Each position must have one distinct Unicode code point. Position zero is
    required to be the blank flap because homing and fallback behavior depend
    on it.
    """

    if not isinstance(value, str):
        raise CharacterSetError("Character set must be text.")

    characters = list(value)
    if len(characters) != FLAP_COUNT:
        raise CharacterSetError(
            "Character set must contain exactly "
            f"{FLAP_COUNT} characters; received {len(characters)}."
        )
    if characters[0] != " ":
        raise CharacterSetError(
            "Character 0 must be a normal space for the black/blank flap."
        )

    control_characters = [
        char for char in characters if unicodedata.category(char).startswith("C")
    ]
    if control_characters:
        raise CharacterSetError(
            "Character set cannot contain line breaks, tabs, or control characters."
        )

    duplicates = []
    seen = set()
    for char in characters:
        if char in seen and char not in duplicates:
            duplicates.append(char)
        seen.add(char)
    if duplicates:
        labels = ", ".join(repr(char) for char in duplicates)
        raise CharacterSetError(
            f"Each flap character must be unique; duplicate: {labels}."
        )

    return "".join(characters)


def firmware_token_for_glyph(glyph, character_set):
    """Return ``(token, index)`` for a physical glyph.

    Unsupported glyphs safely fall back to position zero (the blank flap).
    """

    index = character_set.find(glyph)
    if index < 0:
        index = 0
    return FIRMWARE_CHARACTER_TOKENS[index], index


def display_command_for_index(module_id, index, character_set):
    """Return the safest display command for a physical flap position.

    The legacy character command is retained for the standard reel. Custom
    reels use the numeric index command so Unicode glyphs in a firmware-side
    character map cannot shift later one-byte tokens such as the color flaps.
    """

    module_id = int(module_id)
    index = int(index)
    if index < 0 or index >= FLAP_COUNT:
        raise ValueError(f"Flap index must be between 0 and {FLAP_COUNT - 1}.")

    if character_set == DEFAULT_FLAP_CHARACTER_SET:
        return f"m{module_id:02d}-{FIRMWARE_CHARACTER_TOKENS[index]}"
    return f"m{module_id:02d}+{index}"


def prepare_display_text(
    text,
    character_set,
    module_count,
    raw=False,
    currency_symbol="$",
):
    """Normalize user/app text into physical glyphs for the configured reel."""

    clean_text = str(text)
    # Some phones, browsers, and copied text append an invisible emoji/text
    # presentation selector. It must not consume its own physical flap.
    for selector in EMOJI_VARIATION_SELECTORS:
        clean_text = clean_text.replace(selector, "")

    if not raw:
        clean_text = clean_text.upper()

    for alias, glyph in COLOR_ALIASES.items():
        clean_text = clean_text.replace(alias, glyph)

    currency = str(currency_symbol or "").strip()
    if currency and currency != "$":
        clean_text = clean_text.replace(currency.upper(), "$")

    supported = set(character_set)
    characters = [
        char if char in supported else " "
        for char in clean_text
    ]
    characters = characters[:module_count]
    if len(characters) < module_count:
        characters.extend([" "] * (module_count - len(characters)))
    return "".join(characters)


# Fail at import time if a maintained protocol or preset is accidentally edited
# into an invalid shape.
assert len(FIRMWARE_CHARACTER_TOKENS) == FLAP_COUNT
validate_character_set(DEFAULT_FLAP_CHARACTER_SET)
validate_character_set(ARROW_FLAP_CHARACTER_SET)
