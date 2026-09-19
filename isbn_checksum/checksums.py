"""Checksum math and parsing for ISBN-10, ISBN-13, and EAN-13 barcodes.

Every public function here is pure: given the same input it always returns the
same output, and none of them touch the filesystem, the clock, or global state.
That makes the whole module trivial to test with plain assertions.

Parsing is deliberately split from validity. ``parse_*`` raises ValueError only
for structural problems (wrong length, characters that can't appear in that
format at all) because those mean the input isn't the thing it claims to be.
A checksum mismatch is not treated as unparseable - it's a normal outcome
worth reporting, so it shows up as ``is_valid=False`` on the returned record
instead of an exception.
"""

from dataclasses import dataclass


def normalize(raw: str) -> str:
    """Strip hyphens, spaces, and any other punctuation, uppercase the rest.

    'X' is a legal ISBN-10 check digit, hence the uppercase step.
    """
    return "".join(ch for ch in raw.upper() if ch.isalnum())


def compute_isbn10_check_digit(first_nine: str) -> str:
    """Compute the ISBN-10 check digit for the first nine digits of a book number.

    Weights descend 10..2 across positions 1-9; the result that would make the
    weighted sum (including the check digit at weight 1) divisible by 11 is
    the check digit. A remainder of 10 is written as 'X', not two digits.
    """
    if len(first_nine) != 9 or not first_nine.isdigit():
        raise ValueError(f"expected 9 digits, got {first_nine!r}")
    total = sum((10 - position) * int(digit) for position, digit in enumerate(first_nine))
    remainder = total % 11
    check = (11 - remainder) % 11
    return "X" if check == 10 else str(check)


def compute_mod10_check_digit(digits: str) -> str:
    """Compute the trailing check digit shared by ISBN-13 and EAN-13.

    Weights alternate 1, 3, 1, 3... left to right across the input; the check
    digit is whatever makes the total (mod 10) come out to zero. Works for any
    length input, but ISBN-13/EAN-13 always pass in 12 digits.
    """
    if not digits.isdigit():
        raise ValueError(f"expected digits, got {digits!r}")
    total = sum(int(digit) * (3 if index % 2 else 1) for index, digit in enumerate(digits))
    return str((10 - total % 10) % 10)


@dataclass(frozen=True)
class ParsedISBN10:
    raw: str
    digits: str
    check_digit: str
    is_valid: bool


@dataclass(frozen=True)
class ParsedISBN13:
    raw: str
    digits: str
    check_digit: str
    is_valid: bool


@dataclass(frozen=True)
class ParsedEAN13:
    raw: str
    digits: str
    check_digit: str
    is_valid: bool


@dataclass(frozen=True)
class ParsedUPCA:
    raw: str
    digits: str
    check_digit: str
    is_valid: bool


def compute_upca_check_digit(first_eleven: str) -> str:
    """Compute the UPC-A check digit for the first eleven digits.

    Weights alternate 3, 1, 3, 1... left to right - the mirror image of the
    1, 3, 1, 3... weighting mod10 uses for ISBN-13/EAN-13, since UPC-A has one
    fewer digit before the check digit and starts the pattern on the same foot.
    """
    if len(first_eleven) != 11 or not first_eleven.isdigit():
        raise ValueError(f"expected 11 digits, got {first_eleven!r}")
    total = sum(int(digit) * (3 if index % 2 == 0 else 1) for index, digit in enumerate(first_eleven))
    return str((10 - total % 10) % 10)


def parse_isbn10(raw: str) -> ParsedISBN10:
    digits = normalize(raw)
    if len(digits) != 10:
        raise ValueError(
            f"ISBN-10 must have 10 characters after removing separators, got {len(digits)}"
        )
    body, last = digits[:9], digits[9]
    if not body.isdigit() or not (last.isdigit() or last == "X"):
        raise ValueError(f"ISBN-10 must be 9 digits followed by a digit or 'X', got {digits!r}")
    expected = compute_isbn10_check_digit(body)
    return ParsedISBN10(raw=raw, digits=digits, check_digit=expected, is_valid=expected == last)


def parse_isbn13(raw: str) -> ParsedISBN13:
    digits = normalize(raw)
    if len(digits) != 13 or not digits.isdigit():
        raise ValueError(f"ISBN-13 must be 13 digits after removing separators, got {digits!r}")
    expected = compute_mod10_check_digit(digits[:12])
    return ParsedISBN13(raw=raw, digits=digits, check_digit=expected, is_valid=expected == digits[12])


def parse_ean13(raw: str) -> ParsedEAN13:
    digits = normalize(raw)
    if len(digits) != 13 or not digits.isdigit():
        raise ValueError(f"EAN-13 must be 13 digits after removing separators, got {digits!r}")
    expected = compute_mod10_check_digit(digits[:12])
    return ParsedEAN13(raw=raw, digits=digits, check_digit=expected, is_valid=expected == digits[12])


def parse_upca(raw: str) -> ParsedUPCA:
    digits = normalize(raw)
    if len(digits) != 12 or not digits.isdigit():
        raise ValueError(f"UPC-A must be 12 digits after removing separators, got {digits!r}")
    expected = compute_upca_check_digit(digits[:11])
    return ParsedUPCA(raw=raw, digits=digits, check_digit=expected, is_valid=expected == digits[11])


def parse_isbn(raw: str):
    """Parse an ISBN of either generation, picking the format by length.

    Returns a ParsedISBN10 or ParsedISBN13. Raises ValueError if the input
    normalizes to something other than 10 or 13 characters.
    """
    length = len(normalize(raw))
    if length == 10:
        return parse_isbn10(raw)
    if length == 13:
        return parse_isbn13(raw)
    raise ValueError(f"ISBN must be 10 or 13 characters after removing separators, got {length}")


def is_valid_isbn10(raw: str) -> bool:
    try:
        return parse_isbn10(raw).is_valid
    except ValueError:
        return False


def is_valid_isbn13(raw: str) -> bool:
    try:
        return parse_isbn13(raw).is_valid
    except ValueError:
        return False


def is_valid_ean13(raw: str) -> bool:
    try:
        return parse_ean13(raw).is_valid
    except ValueError:
        return False


def is_valid_upca(raw: str) -> bool:
    try:
        return parse_upca(raw).is_valid
    except ValueError:
        return False


def isbn10_to_isbn13(raw: str) -> ParsedISBN13:
    """Convert an ISBN-10 to the ISBN-13 that identifies the same edition.

    The first nine digits of an ISBN-10 are the actual identifier (group,
    registrant, publication); the tenth is just a check digit derived from
    them. Converting means prefixing those nine digits with "978" (the
    Bookland EAN prefix reserved for books) and computing a fresh check
    digit for the result - the original ISBN-10 check digit is discarded
    entirely rather than reused, so this works the same regardless of
    whether the input's own check digit was correct.

    Raises ValueError only if the input isn't structurally an ISBN-10
    (wrong length or bad characters), matching parse_isbn10.
    """
    parsed10 = parse_isbn10(raw)
    body = "978" + parsed10.digits[:9]
    check = compute_mod10_check_digit(body)
    return ParsedISBN13(raw=raw, digits=body + check, check_digit=check, is_valid=True)


def format_digits(digits: str, group_size: int = 4, separator: str = "-") -> str:
    """Group digits for readability, left to right, in fixed-size chunks.

    This is not official ISBN/EAN hyphenation - real hyphen placement depends
    on a registrant-range database (which group, publisher, and title a
    prefix belongs to) that this module doesn't have. It's just a readable
    grouping, useful for display when you don't need the canonical form.
    """
    if group_size <= 0:
        raise ValueError("group_size must be positive")
    groups = [digits[i : i + group_size] for i in range(0, len(digits), group_size)]
    return separator.join(groups)


def format_isbn(parsed, group_size: int = 4, separator: str = "-") -> str:
    """Pretty-print a parsed ISBN-10 or ISBN-13 record. See format_digits caveat."""
    return format_digits(parsed.digits, group_size=group_size, separator=separator)


def format_ean13(parsed: ParsedEAN13, group_size: int = 4, separator: str = "-") -> str:
    """Pretty-print a parsed EAN-13 record. See format_digits caveat."""
    return format_digits(parsed.digits, group_size=group_size, separator=separator)


def format_upca(parsed: ParsedUPCA, group_size: int = 4, separator: str = "-") -> str:
    """Pretty-print a parsed UPC-A record. See format_digits caveat."""
    return format_digits(parsed.digits, group_size=group_size, separator=separator)
