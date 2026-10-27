import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent / "contacts.db"


@dataclass
class Contact:
    """Represents a single contact entry with basic phone validation."""

    name: str
    phone: str
    email: str = ""

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        self.phone = self.validate_phone(self.phone)
        self.email = self.email.strip()
        if not self.name:
            raise ValueError("Contact name cannot be empty.")

    @staticmethod
    def validate_phone(phone: str) -> str:
        """Validates and normalizes a phone number (allows '+' and 7-15 digits)."""
        cleaned = re.sub(r"[\s\-\(\)]", "", phone.strip())
        if not re.fullmatch(r"\+?\d{7,15}", cleaned):
            raise ValueError(
                "Invalid phone number. Use 7-15 digits (optional '+' prefix)."
            )
        return cleaned


class AddressBook:
    """Manages contacts in a local SQLite database (full CRUD operations)."""

    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH) -> None:
        self.conn = sqlite3.connect(db_path)
        self._create_table()

    def _create_table(self) -> None:
        """Creates the contacts table if it does not exist yet."""
        query = """
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE COLLATE NOCASE,
            phone TEXT NOT NULL,
            email TEXT DEFAULT ''
        );
        """
        self.conn.execute(query)
        self.conn.commit()

    def add(self, contact: Contact) -> None:
        """Inserts a new contact into the database."""
        try:
            self.conn.execute(
                "INSERT INTO contacts (name, phone, email) VALUES (?, ?, ?)",
                (contact.name, contact.phone, contact.email),
            )
            self.conn.commit()
        except sqlite3.IntegrityError:
            raise ValueError(f"Contact '{contact.name}' already exists.")

    def update(self, name: str, new_phone: str, new_email: str | None = None) -> None:
        """Updates the phone number (and optionally email) of an existing contact."""
        validated_phone = Contact.validate_phone(new_phone)
        existing = self.get(name)

        email_to_save = existing.email if new_email is None else new_email.strip()
        self.conn.execute(
            "UPDATE contacts SET phone = ?, email = ? WHERE name = ? COLLATE NOCASE",
            (validated_phone, email_to_save, name.strip()),
        )
        self.conn.commit()

    def get(self, name: str) -> Contact:
        """Retrieves a single contact by exact name (case-insensitive)."""
        cursor = self.conn.execute(
            "SELECT name, phone, email FROM contacts WHERE name = ? COLLATE NOCASE",
            (name.strip(),),
        )
        row = cursor.fetchone()
        if row is None:
            raise KeyError(name)
        return Contact(name=row[0], phone=row[1], email=row[2])

    def delete(self, name: str) -> None:
        """Deletes a contact by name. Raises KeyError if not found."""
        cursor = self.conn.execute(
            "DELETE FROM contacts WHERE name = ? COLLATE NOCASE",
            (name.strip(),),
        )
        self.conn.commit()
        if cursor.rowcount == 0:
            raise KeyError(name)

    def search(self, query_text: str) -> list[Contact]:
        """Searches contacts by partial name, phone, or email."""
        pattern = f"%{query_text.strip()}%"
        cursor = self.conn.execute(
            """
            SELECT name, phone, email
            FROM contacts
            WHERE name LIKE ? OR phone LIKE ? OR email LIKE ?
            ORDER BY name ASC
            """,
            (pattern, pattern, pattern),
        )
        return [Contact(name=r[0], phone=r[1], email=r[2]) for r in cursor.fetchall()]

    def get_all(self) -> list[Contact]:
        """Returns all stored contacts sorted alphabetically by name."""
        cursor = self.conn.execute(
            "SELECT name, phone, email FROM contacts ORDER BY name ASC"
        )
        return [Contact(name=r[0], phone=r[1], email=r[2]) for r in cursor.fetchall()]

    def close(self) -> None:
        """Closes the database connection."""
        self.conn.close()
