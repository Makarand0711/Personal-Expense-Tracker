import os
import unittest
from expense_manager import ExpenseManager
from models import Expense
from storage import JSONStorage


class TestExpenseTracker(unittest.TestCase):
    """Unit test suite for Expense Tracker application."""

    def setUp(self) -> None:
        """Sets up a temporary storage and manager before each test."""
        self.test_file = "test_expenses.json"
        self.storage = JSONStorage(self.test_file)
        self.manager = ExpenseManager(self.storage)

    def tearDown(self) -> None:
        """Cleans up temporary test files after each test."""
        for file in [
            self.test_file,
            f"{self.test_file}.bak",
            f"{self.test_file}.tmp",
            f"{self.test_file}.corrupted",
        ]:
            if os.path.exists(file):
                try:
                    os.remove(file)
                except Exception:
                    pass

    def test_add_expense(self) -> None:
        """Tests adding valid expenses and validating incorrect inputs."""
        # Test valid add
        expense = self.manager.add_expense("Lunch", 15.50, "Food", "2026-06-25")
        self.assertEqual(len(self.manager.expenses), 1)
        self.assertEqual(expense.title, "Lunch")
        self.assertEqual(expense.amount, 15.50)
        self.assertEqual(expense.category, "Food")
        self.assertEqual(expense.date, "2026-06-25")
        self.assertIsNotNone(expense.id)

        # Test invalid titles (empty or whitespace)
        with self.assertRaises(ValueError):
            self.manager.add_expense("", 10.0, "Food", "2026-06-25")
        with self.assertRaises(ValueError):
            self.manager.add_expense("   ", 10.0, "Food", "2026-06-25")

        # Test invalid amounts (negative, zero, or non-numeric)
        with self.assertRaises(ValueError):
            self.manager.add_expense("Lunch", -5.0, "Food", "2026-06-25")
        with self.assertRaises(ValueError):
            self.manager.add_expense("Lunch", 0.0, "Food", "2026-06-25")

        # Test invalid category
        with self.assertRaises(ValueError):
            self.manager.add_expense("Lunch", 10.0, "", "2026-06-25")

        # Test invalid date formats
        with self.assertRaises(ValueError):
            self.manager.add_expense("Lunch", 10.0, "Food", "invalid-date")
        with self.assertRaises(ValueError):
            self.manager.add_expense("Lunch", 10.0, "Food", "25-06-2026")

    def test_delete_expense(self) -> None:
        """Tests deleting existing and non-existing expenses."""
        e1 = self.manager.add_expense("Lunch", 15.50, "Food", "2026-06-25")
        e2 = self.manager.add_expense("Bus Fare", 3.00, "Transport", "2026-06-26")

        self.assertEqual(len(self.manager.expenses), 2)

        # Test deleting existing expense
        success = self.manager.delete_expense(e1.id)
        self.assertTrue(success)
        self.assertEqual(len(self.manager.expenses), 1)
        self.assertIsNone(self.manager.get_expense_by_id(e1.id))

        # Test deleting non-existing expense
        success2 = self.manager.delete_expense("non-existing-id")
        self.assertFalse(success2)
        self.assertEqual(len(self.manager.expenses), 1)

    def test_search_expense(self) -> None:
        """Tests searching expenses by title, category, and date (case-insensitively)."""
        self.manager.add_expense("Coffee break", 4.50, "Food", "2026-06-25")
        self.manager.add_expense("Weekly groceries", 120.00, "Food", "2026-06-26")
        self.manager.add_expense("Taxi ride", 25.00, "Transport", "2026-06-27")

        # Search by title (partial match, case-insensitive)
        results = self.manager.search_expenses("groceries", "title")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Weekly groceries")

        # Search by category (case-insensitive match)
        results2 = self.manager.search_expenses("FOOD", "category")
        self.assertEqual(len(results2), 2)

        # Search by date (exact match)
        results3 = self.manager.search_expenses("2026-06-27", "date")
        self.assertEqual(len(results3), 1)
        self.assertEqual(results3[0].title, "Taxi ride")

        # Search with invalid search type
        with self.assertRaises(ValueError):
            self.manager.search_expenses("Food", "invalid_type")

    def test_monthly_summary(self) -> None:
        """Tests computing totals, category breakdown, and highest/average for a month."""
        self.manager.add_expense("Lunch", 15.00, "Food", "2026-06-01")
        self.manager.add_expense("Dinner", 45.00, "Food", "2026-06-15")
        self.manager.add_expense("Gas", 30.00, "Transport", "2026-06-20")
        self.manager.add_expense("July rent", 1000.00, "Rent", "2026-07-01")

        # Monthly summary for June 2026
        summary = self.manager.get_monthly_summary(2026, 6)
        self.assertEqual(summary["total"], 90.00)
        self.assertEqual(summary["count"], 3)
        self.assertEqual(summary["average"], 30.00)
        self.assertEqual(summary["highest"].title, "Dinner")
        self.assertEqual(summary["by_category"]["Food"], 60.00)
        self.assertEqual(summary["by_category"]["Transport"], 30.00)

        # Monthly summary for empty month
        empty_summary = self.manager.get_monthly_summary(2026, 8)
        self.assertEqual(empty_summary["total"], 0.0)
        self.assertEqual(empty_summary["count"], 0)
        self.assertIsNone(empty_summary["highest"])

    def test_load_and_save_operations(self) -> None:
        """Tests files save, load, and data recovery for corrupted files."""
        # Check fresh state
        self.assertEqual(len(self.manager.expenses), 0)

        # Save an expense, checking file creation
        self.manager.add_expense("Book", 12.99, "Education", "2026-06-26")
        self.assertTrue(os.path.exists(self.test_file))

        # Re-initialize another manager with the same file to verify loading
        new_manager = ExpenseManager(self.storage)
        self.assertEqual(len(new_manager.expenses), 1)
        self.assertEqual(new_manager.expenses[0].title, "Book")

        # Test corrupt JSON handling when no backup exists
        with open(self.test_file, "w") as f:
            f.write("corrupted { text }")

        # Re-initialize new storage so backup path is clean
        if os.path.exists(f"{self.test_file}.bak"):
            os.remove(f"{self.test_file}.bak")

        corrupt_storage = JSONStorage(self.test_file)
        with self.assertRaises(ValueError):
            corrupt_storage.load_expenses()

        # Test corrupted JSON recovery when a valid backup DOES exist
        # Remove the corrupted file first to start fresh
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
            
        # 1. Create a valid state & save (adding two expenses triggers the backup creation)
        valid_storage = JSONStorage(self.test_file)
        valid_manager = ExpenseManager(valid_storage)
        valid_manager.add_expense("Phone", 50.00, "Utilities", "2026-06-01")
        valid_manager.add_expense("Internet", 30.00, "Utilities", "2026-06-02")

        # 2. Corrupt the main file
        with open(self.test_file, "w") as f:
            f.write("{bad-json:")

        # 3. Loading should heal the main file using the backup file (which has "Phone")
        recovered_list = valid_storage.load_expenses()
        self.assertEqual(len(recovered_list), 1)
        self.assertEqual(recovered_list[0].title, "Phone")

        # Verify the main file is formatted properly again
        with open(self.test_file, "r") as f:
            raw_content = f.read()
            self.assertIn("Phone", raw_content)
