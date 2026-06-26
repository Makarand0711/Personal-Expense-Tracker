from __future__ import annotations
import csv
import uuid
from collections import Counter
from typing import Any, Dict, List
from models import Expense
from storage import JSONStorage


class ExpenseManager:
    """Manages the operations and calculations on the collection of expenses."""

    def __init__(self, storage: JSONStorage) -> None:
        """Initializes ExpenseManager with storage.

        Args:
            storage: The JSONStorage system used to load and save data.
        """
        self.storage: JSONStorage = storage
        self.expenses: List[Expense] = []
        self.load_expenses()

    def load_expenses(self) -> None:
        """Loads expenses from storage into memory."""
        self.expenses = self.storage.load_expenses()

    def save_expenses(self) -> None:
        """Saves current memory state of expenses to storage."""
        self.storage.save_expenses(self.expenses)

    def add_expense(
        self, title: str, amount: float, category: str, date: str
    ) -> Expense:
        """Validates, creates, and saves a new expense.

        Args:
            title: The title/description of the expense.
            amount: The cost of the expense.
            category: The category of the expense.
            date: The date when the expense occurred (YYYY-MM-DD).

        Returns:
            The created Expense object.

        Raises:
            ValueError: If validation checks fail.
        """
        expense = Expense(title=title, amount=amount, category=category, date=date)
        self.expenses.append(expense)
        self.save_expenses()
        return expense

    def get_expense_by_id(self, expense_id: str) -> Expense | None:
        """Retrieves an expense by its unique ID.

        Args:
            expense_id: The unique ID string to search for.

        Returns:
            The matching Expense object, or None if not found.
        """
        for expense in self.expenses:
            if expense.id == expense_id:
                return expense
        return None

    def update_expense(
        self,
        expense_id: str,
        title: str | None = None,
        amount: float | None = None,
        category: str | None = None,
        date: str | None = None,
    ) -> Expense:
        """Updates fields of an existing expense.

        Only parameters that are not None will be updated. Setters handle validation.

        Args:
            expense_id: The ID of the expense to update.
            title: New title, or None.
            amount: New amount, or None.
            category: New category, or None.
            date: New date, or None.

        Returns:
            The updated Expense object.

        Raises:
            ValueError: If the expense ID does not exist or if values are invalid.
        """
        expense = self.get_expense_by_id(expense_id)
        if not expense:
            raise ValueError(f"Expense with ID '{expense_id}' not found.")

        # Update values if provided (trigger properties validation)
        if title is not None:
            expense.title = title
        if amount is not None:
            expense.amount = amount
        if category is not None:
            expense.category = category
        if date is not None:
            expense.date = date

        self.save_expenses()
        return expense

    def delete_expense(self, expense_id: str) -> bool:
        """Deletes an expense by its ID.

        Args:
            expense_id: The ID of the expense to delete.

        Returns:
            True if the expense was found and deleted, False otherwise.
        """
        expense = self.get_expense_by_id(expense_id)
        if expense:
            self.expenses.remove(expense)
            self.save_expenses()
            return True
        return False

    def get_all_expenses(
        self, sort_by: str | None = None, reverse: bool = False
    ) -> List[Expense]:
        """Returns all expenses, optionally sorted.

        Args:
            sort_by: Property name to sort by ('date', 'amount', 'title',
              'category').
            reverse: Sort in descending order if True.

        Returns:
            A list of Expense objects.

        Raises:
            ValueError: If sort_by is not a valid attribute name.
        """
        if not sort_by:
            return self.expenses

        valid_sort_keys = {"date", "amount", "title", "category"}
        if sort_by not in valid_sort_keys:
            raise ValueError(f"Invalid sort key. Choose from: {valid_sort_keys}")

        return sorted(
            self.expenses, key=lambda x: getattr(x, sort_by), reverse=reverse
        )

    def search_expenses(self, query: str, search_type: str) -> List[Expense]:
        """Searches for expenses matching a query under a specified category.

        Args:
            query: The search term (e.g. partial title, category name, or YYYY-MM
              date).
            search_type: The attribute type to filter ('title', 'category',
              'date').

        Returns:
            A list of matching Expense objects.

        Raises:
            ValueError: If search_type is not 'title', 'category', or 'date'.
        """
        q = query.lower().strip()
        search_type = search_type.lower().strip()

        if search_type not in {"title", "category", "date"}:
            raise ValueError("Search type must be 'title', 'category', or 'date'.")

        results = []
        for expense in self.expenses:
            if search_type == "title" and q in expense.title.lower():
                results.append(expense)
            elif search_type == "category" and q in expense.category.lower():
                results.append(expense)
            elif search_type == "date" and q in expense.date.lower():
                # Allow partial date matches (e.g., "2026-06" to match all June 2026 dates)
                results.append(expense)

        return results

    def get_monthly_summary(self, year: int, month: int) -> Dict[str, Any]:
        """Calculates a summary of expenses for a specific month and year.

        Args:
            year: Year integer.
            month: Month integer (1-12).

        Returns:
            A dictionary containing:
            - "total": Sum of all expenses in the month.
            - "by_category": Dictionary with category totals.
            - "highest": The highest single Expense object, or None.
            - "average": Average expense amount in the month.
            - "count": Total count of expenses in the month.
        """
        prefix = f"{year:04d}-{month:02d}"
        monthly_expenses = [e for e in self.expenses if e.date.startswith(prefix)]

        if not monthly_expenses:
            return {
                "total": 0.0,
                "by_category": {},
                "highest": None,
                "average": 0.0,
                "count": 0,
            }

        total = sum(e.amount for e in monthly_expenses)
        count = len(monthly_expenses)
        average = total / count

        by_category: Dict[str, float] = {}
        for e in monthly_expenses:
            by_category[e.category] = by_category.get(e.category, 0.0) + e.amount

        highest = max(monthly_expenses, key=lambda x: x.amount)

        return {
            "total": total,
            "by_category": by_category,
            "highest": highest,
            "average": average,
            "count": count,
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Computes general statistics of all expenses.

        Returns:
            A dictionary containing:
            - "count": Total number of expenses.
            - "most_used_category": The category used most frequently.
            - "monthly_spending": Chronologically sorted dict of monthly
            spending (key "YYYY-MM" to value float).
        """
        if not self.expenses:
            return {"count": 0, "most_used_category": None, "monthly_spending": {}}

        count = len(self.expenses)

        # Most used category by count
        categories = [e.category for e in self.expenses]
        most_used_category = Counter(categories).most_common(1)[0][0]

        # Monthly spending breakdown
        monthly_spending: Dict[str, float] = {}
        for e in self.expenses:
            month_key = e.date[:7]  # Get YYYY-MM
            monthly_spending[month_key] = (
                monthly_spending.get(month_key, 0.0) + e.amount
            )

        # Sort chronologically by the YYYY-MM key
        sorted_monthly = dict(sorted(monthly_spending.items()))

        return {
            "count": count,
            "most_used_category": most_used_category,
            "monthly_spending": sorted_monthly,
        }

    def export_to_csv(self, csv_path: str) -> None:
        """Exports all expenses to a CSV file.

        Args:
            csv_path: The file path to save the CSV.

        Raises:
            IOError: If writing to the CSV fails.
        """
        try:
            with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    ["ID", "Title", "Amount", "Category", "Date", "Created At"]
                )
                for e in self.expenses:
                    writer.writerow(
                        [e.id, e.title, e.amount, e.category, e.date, e.created_at]
                    )
        except Exception as e:
            raise IOError(f"Failed to export CSV: {e}")

    def import_from_csv(self, csv_path: str) -> int:
        """Imports expenses from a CSV file.

        Validates CSV content and fields. Automatically resolves ID conflicts.

        Args:
            csv_path: The file path to import the CSV from.

        Returns:
            The number of expenses imported.

        Raises:
            ValueError: If file is empty, headers are missing, or records are
              invalid.
        """
        imported_count = 0
        new_expenses: List[Expense] = []

        try:
            with open(csv_path, mode="r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if not header:
                    raise ValueError("CSV file is empty.")

                header_lower = [
                    h.lower().replace(" ", "").replace("_", "") for h in header
                ]

                # Map header indices
                try:
                    title_idx = header_lower.index("title")
                    amount_idx = header_lower.index("amount")
                    category_idx = header_lower.index("category")
                    date_idx = header_lower.index("date")
                except ValueError:
                    raise ValueError(
                        "CSV must contain 'Title', 'Amount', 'Category', and 'Date' columns."
                    )

                id_idx = header_lower.index("id") if "id" in header_lower else None
                created_at_idx = (
                    header_lower.index("createdat")
                    if "createdat" in header_lower
                    else None
                )

                for row_idx, row in enumerate(reader, start=2):
                    if not row or all(v.strip() == "" for v in row):
                        continue  # Skip blank lines

                    if len(row) <= max(title_idx, amount_idx, category_idx, date_idx):
                        raise ValueError(f"Row {row_idx} is missing columns.")

                    title = row[title_idx]
                    category = row[category_idx]
                    date = row[date_idx]

                    try:
                        amount = float(row[amount_idx])
                    except ValueError:
                        raise ValueError(
                            f"Row {row_idx}: Amount '{row[amount_idx]}' must be numeric."
                        )

                    expense_id = (
                        row[id_idx]
                        if (
                            id_idx is not None
                            and len(row) > id_idx
                            and row[id_idx].strip()
                        )
                        else None
                    )
                    created_at = (
                        row[created_at_idx]
                        if (
                            created_at_idx is not None
                            and len(row) > created_at_idx
                            and row[created_at_idx].strip()
                        )
                        else None
                    )

                    try:
                        expense = Expense(
                            title=title,
                            amount=amount,
                            category=category,
                            date=date,
                            id=expense_id,
                            created_at=created_at,
                        )
                        new_expenses.append(expense)
                    except ValueError as e:
                        raise ValueError(f"Row {row_idx} data invalid: {e}")

            # Merge imported items in
            existing_ids = {e.id for e in self.expenses}
            for e in new_expenses:
                if e.id in existing_ids:
                    # Resolve ID collision dynamically
                    e.id = uuid.uuid4().hex
                self.expenses.append(e)
                imported_count += 1

            if imported_count > 0:
                self.save_expenses()

            return imported_count

        except Exception as e:
            raise ValueError(f"Error during CSV import: {e}")
