from __future__ import annotations
import os
import sys
from datetime import datetime
from typing import Any, Callable, List
from colorama import Back, Fore, Style, init

from expense_manager import ExpenseManager
from models import Expense
from storage import JSONStorage

# Initialize colorama with auto-reset for colors
init(autoreset=True)


def print_header(title: str) -> None:
    """Prints a formatted menu header in color."""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'=' * 10} {title} {'=' * 10}\n")


def print_success(message: str) -> None:
    """Prints a green check success message."""
    print(f"{Fore.GREEN}✔ {message}")


def print_error(message: str) -> None:
    """Prints a red error message."""
    print(f"{Fore.RED}✘ Error: {message}")


def print_warning(message: str) -> None:
    """Prints a yellow warning message."""
    print(f"{Fore.YELLOW}⚠ Warning: {message}")


def get_input(
    prompt: str,
    validator: Callable[[str], Any] | None = None,
    default: str | None = None,
    allow_empty: bool = False,
) -> Any:
    """Prompts user for input, validates it, and returns the parsed value.

    If a default is provided, it is returned if the user presses enter.
    If allow_empty is True, empty inputs return empty strings.
    """
    prompt_suffix = f" [Default: {default}]" if default is not None else ""
    full_prompt = f"{Fore.BLUE}{prompt}{prompt_suffix}: {Style.RESET_ALL}"

    while True:
        try:
            user_input = input(full_prompt).strip()
            if not user_input:
                if default is not None:
                    if validator:
                        return validator(default)
                    return default
                if allow_empty:
                    return ""
                raise ValueError("Input cannot be empty.")

            if validator:
                return validator(user_input)
            return user_input
        except ValueError as e:
            print_error(str(e))


# Validators for UI Inputs
def validate_date(date_str: str) -> str:
    """Validates date input is in YYYY-MM-DD format."""
    date_str = date_str.strip()
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except ValueError:
        raise ValueError(
            "Invalid date format. Please use YYYY-MM-DD (e.g. 2026-06-26)."
        )


def validate_amount(amount_str: str) -> float:
    """Validates amount input is a positive float."""
    amount_str = amount_str.strip()
    try:
        val = float(amount_str)
    except ValueError:
        raise ValueError("Amount must be a numeric value.")
    if val <= 0:
        raise ValueError("Amount must be greater than zero.")
    return val


def validate_non_empty(text: str) -> str:
    """Validates input is a non-empty string."""
    text = text.strip()
    if not text:
        raise ValueError("This field cannot be empty.")
    return text


def validate_year(year_str: str) -> int:
    """Validates year is a 4-digit integer."""
    try:
        year = int(year_str)
        if year < 1000 or year > 9999:
            raise ValueError
        return year
    except ValueError:
        raise ValueError("Year must be a 4-digit number (e.g. 2026).")


def validate_month(month_str: str) -> int:
    """Validates month is between 1 and 12."""
    try:
        month = int(month_str)
        if month < 1 or month > 12:
            raise ValueError
        return month
    except ValueError:
        raise ValueError("Month must be a number between 1 and 12.")


def print_expense_table(expenses: List[Expense]) -> None:
    """Draws a beautiful dynamically-sized table displaying expenses."""
    if not expenses:
        print_warning("No expenses to display.")
        return

    # Define base column widths
    id_w = 8
    title_w = max(len("Title"), max(len(e.title) for e in expenses))
    amount_w = max(len("Amount"), max(len(f"${e.amount:,.2f}") for e in expenses))
    category_w = max(len("Category"), max(len(e.category) for e in expenses))
    date_w = max(len("Date"), max(len(e.date) for e in expenses))

    # Add spacing padding
    title_w += 2
    amount_w += 2
    category_w += 2
    date_w += 2

    # Draw border
    border = (
        f"+{'-' * (id_w + 2)}+{'-' * title_w}+{'-' * amount_w}"
        f"+{'-' * category_w}+{'-' * date_w}+"
    )

    print(border)
    print(
        f"| {Fore.CYAN}{Style.BRIGHT}{'ID':<{id_w}}{Style.RESET_ALL} | "
        f"{Fore.CYAN}{Style.BRIGHT}{'Title':<{title_w-2}}{Style.RESET_ALL} | "
        f"{Fore.CYAN}{Style.BRIGHT}{'Amount':<{amount_w-2}}{Style.RESET_ALL} | "
        f"{Fore.CYAN}{Style.BRIGHT}{'Category':<{category_w-2}}{Style.RESET_ALL} | "
        f"{Fore.CYAN}{Style.BRIGHT}{'Date':<{date_w-2}}{Style.RESET_ALL} |"
    )
    print(border)

    for idx, e in enumerate(expenses):
        id_str = e.id[:id_w]
        title_str = e.title
        amount_str = f"${e.amount:,.2f}"
        category_str = e.category
        date_str = e.date

        # Alternating row colors for layout readability
        row_color = Fore.WHITE if idx % 2 == 0 else Fore.LIGHTWHITE_EX
        amount_color = Fore.GREEN if idx % 2 == 0 else Fore.LIGHTGREEN_EX
        print(
            f"| {row_color}{id_str:<{id_w}}{Style.RESET_ALL} | "
            f"{row_color}{title_str:<{title_w-2}}{Style.RESET_ALL} | "
            f"{amount_color}{amount_str:>{amount_w-2}}{Style.RESET_ALL} | "
            f"{row_color}{category_str:<{category_w-2}}{Style.RESET_ALL} | "
            f"{row_color}{date_str:<{date_w-2}}{Style.RESET_ALL} |"
        )
    print(border)


def find_expense_by_prefix_or_id(
    manager: ExpenseManager, id_input: str
) -> Expense | None:
    """Finds an expense using prefix matching of IDs (user friendliness)."""
    id_input = id_input.strip()
    if not id_input:
        return None

    # Try exact match first
    exact = manager.get_expense_by_id(id_input)
    if exact:
        return exact

    # Try prefix matching
    matches = [e for e in manager.expenses if e.id.startswith(id_input)]
    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        print_warning(f"Multiple expenses match ID prefix '{id_input}':")
        for m in matches:
            print(
                f" - {m.id[:8]} | {m.title} | ${m.amount:.2f} | {m.category} | {m.date}"
            )
        raise ValueError("Multiple matches found. Please enter a longer ID prefix.")

    return None


def handle_view_expenses(manager: ExpenseManager) -> None:
    """Handles option 2: viewing expenses with sorting, pagination, CSV exports."""
    page_size = 10
    current_page = 1
    sort_by = "date"
    reverse = True  # Default: newest first

    while True:
        expenses = manager.get_all_expenses(sort_by=sort_by, reverse=reverse)
        total_expenses = len(expenses)

        if total_expenses == 0:
            print_warning("\nNo expenses recorded yet. Choose Option 1 to add one.")
            return

        total_pages = (total_expenses + page_size - 1) // page_size

        if current_page > total_pages:
            current_page = total_pages
        if current_page < 1:
            current_page = 1

        start_idx = (current_page - 1) * page_size
        end_idx = start_idx + page_size
        page_expenses = expenses[start_idx:end_idx]

        print_header(f"View Expenses (Page {current_page} of {total_pages})")
        print(
            f"{Fore.LIGHTBLACK_EX}Sorted by: {sort_by.upper()} "
            f"({'DESC' if reverse else 'ASC'}) | Total: {total_expenses} expense(s)"
        )
        print_expense_table(page_expenses)

        # Build sub-menu options
        options = []
        if current_page < total_pages:
            options.append(f"{Fore.YELLOW}[N] Next Page{Style.RESET_ALL}")
        if current_page > 1:
            options.append(f"{Fore.YELLOW}[P] Previous Page{Style.RESET_ALL}")
        options.extend(
            [
                f"{Fore.YELLOW}[S] Sort Expenses{Style.RESET_ALL}",
                f"{Fore.YELLOW}[E] Export CSV{Style.RESET_ALL}",
                f"{Fore.YELLOW}[I] Import CSV{Style.RESET_ALL}",
                f"{Fore.YELLOW}[B] Back to Menu{Style.RESET_ALL}",
            ]
        )

        print(" | ".join(options))
        choice = (
            input(f"{Fore.BLUE}Select option (default: B): {Style.RESET_ALL}")
            .strip()
            .upper()
        )

        if choice == "N" and current_page < total_pages:
            current_page += 1
        elif choice == "P" and current_page > 1:
            current_page -= 1
        elif choice == "S":
            print("\nSort options: 1. Date  2. Amount  3. Title  4. Category")
            sort_choice = get_input(
                "Choose sorting field (1-4)",
                lambda x: (
                    int(x) if x in ["1", "2", "3", "4"] else int("invalid")
                ),
                default="1",
            )
            sort_keys = {1: "date", 2: "amount", 3: "title", 4: "category"}
            sort_by = sort_keys[sort_choice]

            order_choice = get_input(
                "Sort order: 1. Descending (newest/highest first)  2. Ascending",
                lambda x: int(x) if x in ["1", "2"] else int("invalid"),
                default="1",
            )
            reverse = order_choice == 1
            current_page = 1
        elif choice == "E":
            csv_file = get_input(
                "Enter CSV export filename",
                validate_non_empty,
                default="expenses_export.csv",
            )
            try:
                manager.export_to_csv(csv_file)
                print_success(f"Expenses exported successfully to '{csv_file}'!")
            except Exception as e:
                print_error(f"Failed to export: {e}")
        elif choice == "I":
            csv_file = get_input(
                "Enter CSV import filename",
                validate_non_empty,
                default="expenses_export.csv",
            )
            if not os.path.exists(csv_file):
                print_error(f"File '{csv_file}' does not exist.")
                continue
            try:
                count = manager.import_from_csv(csv_file)
                print_success(
                    f"Successfully imported {count} expense(s) from '{csv_file}'!"
                )
                current_page = 1
            except Exception as e:
                print_error(f"Import failed: {e}")
        elif choice == "B" or not choice:
            break


def handle_search_expenses(manager: ExpenseManager) -> None:
    """Handles option 3: Searching expenses by category, date, or title."""
    print_header("Search Expenses")
    if not manager.expenses:
        print_warning("No expenses to search.")
        return

    print("Search by: 1. Title  2. Category  3. Date")
    choice = get_input(
        "Choose option (1-3)",
        lambda x: int(x) if x in ["1", "2", "3"] else int("invalid"),
        default="1",
    )
    search_types = {1: "title", 2: "category", 3: "date"}
    search_type = search_types[choice]

    query = get_input(
        f"Enter search query for {search_type.upper()}", validate_non_empty
    )

    results = manager.search_expenses(query, search_type)
    total_results = len(results)

    print_header(f"Search Results ({total_results} match(es) found)")
    if total_results > 0:
        print_expense_table(results)
    else:
        print_warning("No matching expenses found.")


def handle_update_expense(manager: ExpenseManager) -> None:
    """Handles option 4: updating an expense's fields (with prefix matching)."""
    print_header("Update Expense")
    if not manager.expenses:
        print_warning("No expenses to update.")
        return

    try:
        id_input = get_input(
            "Enter ID (or first 8 chars) of the expense to update",
            validate_non_empty,
        )
        expense = find_expense_by_prefix_or_id(manager, id_input)
        if not expense:
            print_error(f"No expense found with ID/prefix '{id_input}'.")
            return
    except ValueError as e:
        print_error(str(e))
        return

    print(f"\n{Fore.LIGHTBLACK_EX}Updating expense:")
    print(
        f"ID: {expense.id} | Current: {expense.title} | "
        f"${expense.amount:.2f} | {expense.category} | {expense.date}\n"
    )
    print(f"{Fore.YELLOW}(Press Enter to keep current value){Style.RESET_ALL}\n")

    title = get_input("New Title", allow_empty=True)
    title = title if title else None

    amount = None
    while True:
        amount_input = get_input("New Amount", allow_empty=True)
        if not amount_input:
            break
        try:
            amount = validate_amount(amount_input)
            break
        except ValueError as e:
            print_error(str(e))

    category = get_input("New Category", allow_empty=True)
    category = category if category else None

    date = None
    while True:
        date_input = get_input("New Date (YYYY-MM-DD)", allow_empty=True)
        if not date_input:
            break
        try:
            date = validate_date(date_input)
            break
        except ValueError as e:
            print_error(str(e))

    try:
        updated = manager.update_expense(
            expense_id=expense.id,
            title=title,
            amount=amount,
            category=category,
            date=date,
        )
        print_success("Expense updated successfully!")
        print_expense_table([updated])
    except Exception as e:
        print_error(f"Failed to update expense: {e}")


def handle_delete_expense(manager: ExpenseManager) -> None:
    """Handles option 5: deleting an expense (with confirmation)."""
    print_header("Delete Expense")
    if not manager.expenses:
        print_warning("No expenses to delete.")
        return

    try:
        id_input = get_input(
            "Enter ID (or first 8 chars) of the expense to delete",
            validate_non_empty,
        )
        expense = find_expense_by_prefix_or_id(manager, id_input)
        if not expense:
            print_error(f"No expense found with ID/prefix '{id_input}'.")
            return
    except ValueError as e:
        print_error(str(e))
        return

    print(f"\n{Fore.LIGHTBLACK_EX}Confirm deleting expense:")
    print(
        f"ID: {expense.id} | {expense.title} | "
        f"${expense.amount:.2f} | {expense.category} | {expense.date}\n"
    )

    confirm = get_input(
        "Are you sure you want to delete this expense? (y/n)",
        lambda x: (
            x.lower()
            if x.lower() in ["y", "n", "yes", "no"]
            else str(int("invalid"))
        ),
        default="n",
    )
    if confirm in ["y", "yes"]:
        if manager.delete_expense(expense.id):
            print_success("Expense deleted successfully!")
        else:
            print_error("Failed to delete expense.")
    else:
        print_warning("Deletion cancelled.")


def handle_monthly_summary(manager: ExpenseManager) -> None:
    """Handles option 6: Calculates and prints monthly summary breakdown."""
    print_header("Monthly Summary")
    if not manager.expenses:
        print_warning("No expenses to summarize.")
        return

    current_year = datetime.now().year
    current_month = datetime.now().month

    year = get_input("Enter Year (YYYY)", validate_year, default=str(current_year))
    month = get_input("Enter Month (1-12)", validate_month, default=str(current_month))

    summary = manager.get_monthly_summary(year, month)

    print_header(f"Summary for {year:04d}-{month:02d}")
    if summary["count"] == 0:
        print_warning("No expenses recorded for this month.")
        return

    print(f"{Fore.CYAN}Total Spending:     {Fore.GREEN}${summary['total']:,.2f}")
    print(f"{Fore.CYAN}Average Expense:    {Fore.GREEN}${summary['average']:,.2f}")
    print(f"{Fore.CYAN}Total Transactions: {Fore.WHITE}{summary['count']}")

    highest = summary["highest"]
    if highest:
        print(
            f"{Fore.CYAN}Highest Expense:    {Fore.YELLOW}{highest.title} "
            f"(${highest.amount:,.2f} on {highest.date})"
        )

    print(f"\n{Fore.CYAN}{Style.BRIGHT}Spending by Category:")
    cat_border = f"+{'-' * 22}+{'-' * 14}+"
    print(cat_border)
    print(f"| {'Category':<20} | {'Total':<12} |")
    print(cat_border)
    for cat, total in sorted(
        summary["by_category"].items(), key=lambda x: x[1], reverse=True
    ):
        print(f"| {cat:<20} | {Fore.GREEN}${total:>10,.2f}{Style.RESET_ALL} |")
    print(cat_border)


def handle_statistics(manager: ExpenseManager) -> None:
    """Handles option 7: prints global statistics and a mini horizontal bar chart."""
    print_header("Overall Expense Statistics")
    stats = manager.get_statistics()

    if stats["count"] == 0:
        print_warning("No expenses recorded yet.")
        return

    print(f"{Fore.CYAN}Total Transaction Count: {Fore.WHITE}{stats['count']}")
    print(
        f"{Fore.CYAN}Most Frequent Category:  {Fore.YELLOW}{stats['most_used_category']}"
    )

    print(f"\n{Fore.CYAN}{Style.BRIGHT}Monthly Spending History:")
    history_border = f"+{'-' * 12}+{'-' * 16}+"
    print(history_border)
    print(f"| {'Month':<10} | {'Total Spending':<14} |")
    print(history_border)

    monthly_spending = stats["monthly_spending"]
    max_month_spend = max(monthly_spending.values()) if monthly_spending else 1.0

    for month, total in monthly_spending.items():
        bar_len = int((total / max_month_spend) * 10)
        bar = "■" * bar_len
        print(
            f"| {month:<10} | {Fore.GREEN}${total:>11,.2f}{Style.RESET_ALL}  "
            f"{Fore.CYAN}{bar:<10}{Style.RESET_ALL} |"
        )
    print(history_border)


def main() -> None:
    """Main function runner initiating storage, recovery validation, and application loop."""
    print_header("Welcome to Personal Expense Tracker")

    storage = JSONStorage("expenses.json")
    try:
        manager = ExpenseManager(storage)
    except ValueError as e:
        print_error("Storage initialization failed.")
        print(f"{Fore.RED}{e}")
        print("\nPossible actions:")
        print(
            "1. Start fresh (renames corrupted file to expenses.json.corrupted "
            "and deletes existing database)"
        )
        print("2. Exit and fix the file manually")

        action = get_input(
            "Choose action (1-2)",
            lambda x: int(x) if x in ["1", "2"] else int("invalid"),
            default="2",
        )
        if action == 1:
            try:
                storage.save_expenses([])
                manager = ExpenseManager(storage)
                print_success(
                    "Database initialized to empty. You can now use the app."
                )
            except Exception as ex:
                print_error(f"Failed to reset database: {ex}")
                sys.exit(1)
        else:
            print_warning("Exiting program for manual recovery.")
            sys.exit(0)
    except IOError as e:
        print_error(f"File IO error during startup: {e}")
        sys.exit(1)

    while True:
        print(
            f"\n{Fore.MAGENTA}{Style.BRIGHT}======== Expense Tracker ========{Style.RESET_ALL}\n"
        )
        print("1. Add Expense")
        print("2. View Expenses")
        print("3. Search Expense")
        print("4. Update Expense")
        print("5. Delete Expense")
        print("6. Monthly Summary")
        print("7. Statistics")
        print("8. Exit")

        choice = get_input(
            "\nSelect Option (1-8)",
            lambda x: (
                int(x)
                if x in [str(i) for i in range(1, 9)]
                else int("invalid selection")
            ),
        )

        if choice == 1:
            print_header("Add New Expense")
            title = get_input("Title", validate_non_empty)
            amount = get_input("Amount", validate_amount)
            category = get_input("Category", validate_non_empty)

            today_str = datetime.now().strftime("%Y-%m-%d")
            date = get_input("Date (YYYY-MM-DD)", validate_date, default=today_str)

            try:
                expense = manager.add_expense(title, amount, category, date)
                print_success(
                    f"Expense '{expense.title}' added successfully "
                    f"with ID prefix '{expense.id[:8]}'!"
                )
            except Exception as e:
                print_error(f"Failed to add expense: {e}")

        elif choice == 2:
            handle_view_expenses(manager)
        elif choice == 3:
            handle_search_expenses(manager)
        elif choice == 4:
            handle_update_expense(manager)
        elif choice == 5:
            handle_delete_expense(manager)
        elif choice == 6:
            handle_monthly_summary(manager)
        elif choice == 7:
            handle_statistics(manager)
        elif choice == 8:
            print_header("Goodbye!")
            print(
                f"{Fore.GREEN}Thank you for using Personal Expense Tracker. "
                "Stay financially healthy!"
            )
            break


if __name__ == "__main__":
    main()
