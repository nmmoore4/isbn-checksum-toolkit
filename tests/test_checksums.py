import pytest

from isbn_checksum import (
    compute_isbn10_check_digit,
    compute_mod10_check_digit,
    compute_upca_check_digit,
    format_digits,
    format_isbn,
    format_upca,
    is_valid_ean13,
    is_valid_isbn10,
    is_valid_isbn13,
    is_valid_upca,
    isbn10_to_isbn13,
    normalize,
    parse_ean13,
    parse_isbn,
    parse_isbn10,
    parse_isbn13,
    parse_upca,
)

# Real, checkable numbers rather than made-up ones, so a copy/paste error in
# this file would fail loudly instead of quietly validating nonsense.
VALID_ISBN10 = "0-306-40615-2"
VALID_ISBN13 = "978-0-306-40615-7"
VALID_EAN13 = "4006381333931"  # Kinder Surprise egg, a commonly cited EAN-13
VALID_UPCA = "036000291452"  # Kellogg's Corn Flakes, a commonly cited UPC-A


def test_normalize_strips_punctuation_and_uppercases():
    assert normalize("0-306-40615-2") == "0306406152"
    assert normalize(" 978 0 306 40615 7 ") == "9780306406157"
    assert normalize("0-8044-2957-x") == "080442957X"


def test_compute_isbn10_check_digit_matches_known_value():
    assert compute_isbn10_check_digit("030640615") == "2"


def test_compute_isbn10_check_digit_can_produce_x():
    # 1*10 + 2*9 + ... + 9*2 = 210, which is 1 mod 11, so the check value is
    # 11 - 1 = 10, written as 'X'.
    assert compute_isbn10_check_digit("123456789") == "X"


def test_compute_isbn10_check_digit_rejects_wrong_length():
    with pytest.raises(ValueError):
        compute_isbn10_check_digit("12345")


def test_compute_mod10_check_digit_matches_known_isbn13():
    assert compute_mod10_check_digit("978030640615") == "7"


def test_compute_mod10_check_digit_matches_known_ean13():
    assert compute_mod10_check_digit("400638133393") == "1"


def test_parse_isbn10_valid():
    record = parse_isbn10(VALID_ISBN10)
    assert record.is_valid
    assert record.digits == "0306406152"
    assert record.check_digit == "2"


def test_parse_isbn10_valid_with_x_check_digit():
    record = parse_isbn10("123456789X")
    assert record.is_valid
    assert record.check_digit == "X"


def test_parse_isbn10_invalid_checksum_does_not_raise():
    record = parse_isbn10("0-306-40615-9")
    assert not record.is_valid
    assert record.check_digit == "2"  # what it should have been


def test_parse_isbn10_wrong_length_raises():
    with pytest.raises(ValueError):
        parse_isbn10("030640615")


def test_parse_isbn10_bad_characters_raise():
    with pytest.raises(ValueError):
        parse_isbn10("03064061XX")  # body must be digits; only the last slot allows 'X'


def test_parse_isbn13_valid():
    record = parse_isbn13(VALID_ISBN13)
    assert record.is_valid
    assert record.digits == "9780306406157"
    assert record.check_digit == "7"


def test_parse_isbn13_invalid_checksum_does_not_raise():
    record = parse_isbn13("978-0-306-40615-8")
    assert not record.is_valid
    assert record.check_digit == "7"


def test_parse_isbn13_wrong_length_raises():
    with pytest.raises(ValueError):
        parse_isbn13("978030640615")


def test_parse_isbn13_non_digit_raises():
    with pytest.raises(ValueError):
        parse_isbn13("978030640615X")


def test_parse_ean13_valid():
    record = parse_ean13(VALID_EAN13)
    assert record.is_valid
    assert record.check_digit == "1"


def test_parse_ean13_invalid_checksum_does_not_raise():
    record = parse_ean13("4006381333939")
    assert not record.is_valid
    assert record.check_digit == "1"


def test_compute_upca_check_digit_matches_known_value():
    assert compute_upca_check_digit("03600029145") == "2"


def test_compute_upca_check_digit_rejects_wrong_length():
    with pytest.raises(ValueError):
        compute_upca_check_digit("12345")


def test_parse_upca_valid():
    record = parse_upca(VALID_UPCA)
    assert record.is_valid
    assert record.digits == "036000291452"
    assert record.check_digit == "2"


def test_parse_upca_invalid_checksum_does_not_raise():
    record = parse_upca("036000291459")
    assert not record.is_valid
    assert record.check_digit == "2"  # what it should have been


def test_parse_upca_wrong_length_raises():
    with pytest.raises(ValueError):
        parse_upca("03600029145")


def test_parse_upca_non_digit_raises():
    with pytest.raises(ValueError):
        parse_upca("03600029145X")


def test_parse_isbn_dispatches_by_length():
    assert isinstance(parse_isbn(VALID_ISBN10), type(parse_isbn10(VALID_ISBN10)))
    assert isinstance(parse_isbn(VALID_ISBN13), type(parse_isbn13(VALID_ISBN13)))


def test_parse_isbn_rejects_other_lengths():
    with pytest.raises(ValueError):
        parse_isbn("12345")


def test_is_valid_helpers_return_bool_not_raise():
    assert is_valid_isbn10(VALID_ISBN10) is True
    assert is_valid_isbn10("not-an-isbn") is False
    assert is_valid_isbn13(VALID_ISBN13) is True
    assert is_valid_isbn13("not-an-isbn") is False
    assert is_valid_ean13(VALID_EAN13) is True
    assert is_valid_ean13("not-an-ean") is False
    assert is_valid_upca(VALID_UPCA) is True
    assert is_valid_upca("not-a-upc") is False


def test_isbn10_to_isbn13_matches_known_pairing():
    converted = isbn10_to_isbn13(VALID_ISBN10)
    assert converted.digits == "9780306406157"
    assert converted.check_digit == "7"
    assert converted.is_valid


def test_isbn10_to_isbn13_ignores_original_check_digit():
    # The tenth digit of an ISBN-10 never carries into the ISBN-13; only the
    # first nine digits (the actual identifier) do, so a wrong check digit on
    # the input still converts to the correct, valid ISBN-13.
    converted = isbn10_to_isbn13("0-306-40615-9")
    assert converted.digits == "9780306406157"
    assert converted.is_valid


def test_isbn10_to_isbn13_rejects_structurally_invalid_input():
    with pytest.raises(ValueError):
        isbn10_to_isbn13("not-an-isbn")


def test_format_digits_groups_left_to_right():
    assert format_digits("0306406152") == "0306-4061-52"
    assert format_digits("0306406152", group_size=3) == "030-640-615-2"
    assert format_digits("0306406152", group_size=4, separator=" ") == "0306 4061 52"


def test_format_digits_rejects_non_positive_group_size():
    with pytest.raises(ValueError):
        format_digits("123", group_size=0)


def test_format_isbn_uses_parsed_digits():
    record = parse_isbn10(VALID_ISBN10)
    assert format_isbn(record) == "0306-4061-52"


def test_format_upca_uses_parsed_digits():
    record = parse_upca(VALID_UPCA)
    assert format_upca(record) == "0360-0029-1452"
