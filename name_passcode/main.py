"""Turn a name into a simple six-digit passcode."""

from __future__ import annotations


def name_to_passcode(name: str, length: int = 6) -> str:
    """Convert a display name into a passcode.

    Each letter becomes its alphabet position, but only the final digit is used
    for numbers above 9. The result is padded with zeros to the requested length.
    """
    cleaned_name = name or ""
    digits: list[str] = []

    for character in cleaned_name.upper():
        if "A" <= character <= "Z":
            position = ord(character) - ord("A") + 1
            digits.append(str(position % 10))

    code = "".join(digits)
    if len(code) >= length:
        return code[:length]
    return code.ljust(length, "0")


def main() -> None:
    user_name = input("Enter your name: ").strip()
    print(f"Your passcode is: {name_to_passcode(user_name)}")


if __name__ == "__main__":
    main()
