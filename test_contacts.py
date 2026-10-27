import pytest

from main import add_contact, change_contact, delete_contact, parse_input, search_contacts, show_phone
from storage import AddressBook


@pytest.fixture
def book() -> AddressBook:
    """Provides a clean in-memory SQLite AddressBook for each test."""
    ab = AddressBook(":memory:")
    yield ab
    ab.close()


def test_parse_input() -> None:
    cmd, args = parse_input("  ADD   Max   +491601234567  ")
    assert cmd == "add"
    assert args == ["Max", "+491601234567"]
    assert parse_input("   ") == ("", [])


def test_add_and_show_contact(book: AddressBook) -> None:
    res = add_contact(["Anna", "+491519876543", "anna@example.de"], book)
    assert res == "Contact 'Anna' added."
    assert show_phone(["anna"], book) == "Anna: +491519876543 | Email: anna@example.de"


def test_invalid_phone_rejected(book: AddressBook) -> None:
    res = add_contact(["Bob", "abc123"], book)
    assert "Invalid phone number" in res


def test_update_contact(book: AddressBook) -> None:
    add_contact(["Lukas", "01701112233"], book)
    res = change_contact(["Lukas", "+491709998877"], book)
    assert res == "Contact 'Lukas' updated."
    assert show_phone(["Lukas"], book) == "Lukas: +491709998877"


def test_search_contacts(book: AddressBook) -> None:
    add_contact(["Markus", "+49891234567", "markus@firma.de"], book)
    add_contact(["Maria", "+498217654321"], book)
    output = search_contacts(["Mar"], book)
    assert "Markus" in output
    assert "Maria" in output


def test_delete_and_missing_contact(book: AddressBook) -> None:
    add_contact(["Tim", "01605554433"], book)
    assert delete_contact(["Tim"], book) == "Contact 'Tim' deleted."
    assert "was not found" in show_phone(["Tim"], book)
