# isbn-checksum-toolkit

ISBN and EAN-13 numbers carry a check digit so a single mistyped or misscanned
digit gets caught instead of silently pointing at the wrong book. ISBN-10 uses
a mod-11 scheme (with 'X' standing in for a check value of 10); ISBN-13 and
EAN-13 barcodes use mod-10 with alternating weights. This library implements
both, plus a couple of pretty-printing helpers, as plain functions with no
hidden state.

## Why a separate parser and validator

`parse_isbn10` / `parse_isbn13` / `parse_ean13` raise `ValueError` only when
the input isn't shaped like the format at all (wrong length, letters where
digits belong). A checksum mismatch isn't an error - it's a normal, expected
outcome, so it comes back as `is_valid=False` on the parsed record instead of
an exception. That way you can tell "this wasn't an ISBN" apart from "this was
an ISBN but someone mistyped a digit."

## Usage

```python
from isbn_checksum import parse_isbn, parse_isbn10, parse_isbn13, format_isbn

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

# Pretty-printing groups digits for readability (not official hyphenation,
# which needs a registrant-range table this library doesn't ship).
format_isbn(record)                      # "0306-4061-52"
format_isbn(record, group_size=3)        # "030-640-615-2"
```

The EAN-13 functions (`parse_ean13`, `is_valid_ean13`, `format_ean13`) use the
same mod-10 math, since ISBN-13 is just an EAN-13 with a reserved prefix.

## Status

Early skeleton: ISBN-10, ISBN-13, and EAN-13 checksum math and parsing are
implemented and correct. Not yet done: UPC-A (its check-digit weights are
offset from EAN-13's, so it needs its own function), a command-line entry
point, and a test suite.

## License

MIT, see LICENSE.
