from functools import wraps
from typing import Callable

from storage import AddressBook, Contact


def input_error(func: Callable) -> Callable:
    """Decorator for centralized CLI user input error handling."""

    @wraps(func)
    def inner(*args, **kwargs) -> str:
        try:
            return func(*args, **kwargs)
        except KeyError as err:
            name = err.args[0] if err.args else "Unknown"
            return f"Error: Contact '{name}' was not found."
        except ValueError as err:
            return f"Error: {err}"
        except IndexError:
            return "Error: Missing arguments. Type 'help' to see command usage."

    return inner


def parse_input(user_input: str) -> tuple[str, list[str]]:
    """Splits raw console input into a lowercase command and argument list."""
    parts = user_input.strip().split()
    if not parts:
        return "", []
    cmd = parts[0].lower()
    args = parts[1:]
    return cmd, args


def format_contacts_table(contacts: list[Contact]) -> str:
    """Formats a list of Contact objects into a readable console table."""
    if not contacts:
        return "No contacts found."

    header = f"{'Name':<20} | {'Phone':<16} | {'Email'}"
    separator = "-" * 60
    rows = [
        f"{c.name:<20} | {c.phone:<16} | {c.email or '-'}"
        for c in contacts
    ]
    return "\n".join([header, separator, *rows])


@input_error
def add_contact(args: list[str], book: AddressBook) -> str:
    """Adds a new contact. Usage: add <name> <phone> [email]"""
    if len(args) < 2:
        raise ValueError("Usage: add <name> <phone> [email]")
    name, phone = args[0], args[1]
    email = args[2] if len(args) > 2 else ""
    contact = Contact(name=name, phone=phone, email=email)
    book.add(contact)
    return f"Contact '{contact.name}' added."


@input_error
def change_contact(args: list[str], book: AddressBook) -> str:
    """Updates an existing contact. Usage: change <name> <new_phone> [new_email]"""
    if len(args) < 2:
        raise ValueError("Usage: change <name> <new_phone> [new_email]")
    name, new_phone = args[0], args[1]
    new_email = args[2] if len(args) > 2 else None
    book.update(name=name, new_phone=new_phone, new_email=new_email)
    return f"Contact '{name}' updated."


@input_error
def show_phone(args: list[str], book: AddressBook) -> str:
    """Shows details of a single contact. Usage: phone <name>"""
    name = args[0]
    contact = book.get(name)
    email_part = f" | Email: {contact.email}" if contact.email else ""
    return f"{contact.name}: {contact.phone}{email_part}"


@input_error
def delete_contact(args: list[str], book: AddressBook) -> str:
    """Deletes a contact by name. Usage: delete <name>"""
    name = args[0]
    book.delete(name)
    return f"Contact '{name}' deleted."


@input_error
def search_contacts(args: list[str], book: AddressBook) -> str:
    """Searches contacts by name, phone, or email. Usage: search <query>"""
    query = args[0]
    results = book.search(query)
    return format_contacts_table(results)


def show_all(book: AddressBook) -> str:
    """Displays all saved contacts in a formatted table."""
    contacts = book.get_all()
    if not contacts:
        return "No contacts stored yet."
    return format_contacts_table(contacts)


def show_help() -> str:
    """Returns a list of supported CLI commands."""
    return (
        "Available commands:\n"
        "  hello                            - Greet the assistant\n"
        "  add <name> <phone> [email]       - Add a new contact\n"
        "  change <name> <phone> [email]    - Update an existing contact\n"
        "  phone <name>                     - Show phone/email for a contact\n"
        "  search <query>                   - Search by name, phone, or email\n"
        "  delete <name>                    - Delete a contact\n"
        "  all                              - List all saved contacts\n"
        "  help                             - Show this help message\n"
        "  exit / close                     - Exit the application"
    )


def main() -> None:
    book = AddressBook()
    print("Welcome to the CLI Contact Manager! (Type 'help' for commands)")

    commands = {
        "hello": lambda _args: "How can I help you?",
        "help": lambda _args: show_help(),
        "add": lambda args: add_contact(args, book),
        "change": lambda args: change_contact(args, book),
        "phone": lambda args: show_phone(args, book),
        "search": lambda args: search_contacts(args, book),
        "delete": lambda args: delete_contact(args, book),
        "all": lambda _args: show_all(book),
    }

    try:
        while True:
            try:
                user_input = input("\n> ")
            except (KeyboardInterrupt, EOFError):
                print("\nGood bye!")
                break

            command, args = parse_input(user_input)
            if not command:
                continue

            if command in ("close", "exit"):
                print("Good bye!")
                break

            handler = commands.get(command)
            if handler:
                print(handler(args))
            else:
                print("Invalid command. Type 'help' to see available commands.")
    finally:
        book.close()


if __name__ == "__main__":
    main()
