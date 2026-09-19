# isbn-checksum-toolkit

ISBN, EAN-13, and UPC-A numbers carry a check digit so a single mistyped or
misscanned digit gets caught instead of silently pointing at the wrong
product. ISBN-10 uses a mod-11 scheme (with 'X' standing in for a check value
of 10); ISBN-13, EAN-13, and UPC-A all use mod-10 with alternating weights,
though UPC-A's weights start on the opposite parity since it has one fewer
digit ahead of the check digit. This library implements all of them, plus a
couple of pretty-printing helpers, as plain functions with no hidden state.

## Why a separate parser and validator

`parse_isbn10` / `parse_isbn13` / `parse_ean13` raise `ValueError` only when
the input isn't shaped like the format at all (wrong length, letters where
digits belong). A checksum mismatch isn't an error - it's a normal, expected
outcome, so it comes back as `is_valid=False` on the parsed record instead of
an exception. That way you can tell "this wasn't an ISBN" apart from "this was
an ISBN but someone mistyped a digit."

## Usage

```python
from isbn_checksum import parse_isbn, parse_isbn10, parse_isbn13, format_isbn, isbn10_to_isbn13

# A canonical example: two editions of the same book.
parse_isbn10("0-306-40615-2").is_valid   # True
parse_isbn13("978-0-306-40615-7").is_valid  # True

# The dispatcher picks ISBN-10 vs ISBN-13 by length.
record = parse_isbn("0-306-40615-2")
record.digits        # "0306406152"
record.check_digit   # "2"

# A typo in the check digit is caught, not raised.
typo = parse_isbn10("0-306-40615-9")
typo.is_valid         # False
typo.check_digit      # "2"  (what it should have been)

# Structurally invalid input raises instead.
parse_isbn10("abc")   # ValueError

# Converting to ISBN-13 drops the ISBN-10 check digit and computes a fresh
# one, since the check digit isn't part of the identifier itself.
isbn10_to_isbn13("0-306-40615-2").digits  # "9780306406157"

# Pretty-printing groups digits for readability (not official hyphenation,
# which needs a registrant-range table this library doesn't ship).
format_isbn(record)                      # "0306-4061-52"
format_isbn(record, group_size=3)        # "030-640-615-2"
```

The EAN-13 functions (`parse_ean13`, `is_valid_ean13`, `format_ean13`) use the
same mod-10 math, since ISBN-13 is just an EAN-13 with a reserved prefix. The
UPC-A functions (`parse_upca`, `is_valid_upca`, `format_upca`) use the same
mod-10 idea, but with weights on the opposite parity - UPC-A has 11 digits
before the check digit instead of 12.

## Testing

```
pip install -e ".[test]"
pytest
```

## Status

Early skeleton: ISBN-10, ISBN-13, EAN-13, and UPC-A checksum math and parsing
are implemented and correct, with a pytest suite covering known-valid and
known-invalid numbers for all four formats. ISBN-10 to ISBN-13 conversion is
also done. Not yet done: a command-line entry point and real
registrant-range hyphenation.

## License

MIT, see LICENSE.
