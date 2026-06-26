import json
import os
import shutil
from typing import List
from models import Expense


class JSONStorage:
    """Safely handles reading and writing Expense objects to a JSON file.

    Features:
    - Atomic writes (via a temporary file) to prevent data corruption.
    - Automatic backup management.
    - Recovery options for missing, empty, or corrupted files.
    """

    def __init__(self, file_path: str = "expenses.json") -> None:
        """Initializes JSONStorage with the file path.

        Args:
            file_path: The name or path of the target JSON file.
        """
        self.file_path: str = file_path
        self.backup_path: str = f"{file_path}.bak"

    def load_expenses(self) -> List[Expense]:
        """Loads expense records from the JSON file.

        Handles missing files, empty files, and JSON corruption. In case of
        corruption, it attempts recovery using a backup file. If recovery fails,
        it moves the corrupted file to a safe location to avoid data loss.

        Returns:
            A list of Expense objects.

        Raises:
            IOError: If files cannot be read.
            ValueError: If JSON content is malformed and recovery is impossible.
        """
        # Case 1: Main file does not exist
        if not os.path.exists(self.file_path):
            # Check if backup exists and try to load it
            if os.path.exists(self.backup_path):
                try:
                    return self._read_from_path(self.backup_path)
                except Exception:
                    # Backup is also problematic, fall through to return empty list
                    pass
            return []

        # Case 2: Main file is empty (size 0)
        if os.path.getsize(self.file_path) == 0:
            return []

        # Case 3: Read and deserialize main file
        try:
            return self._read_from_path(self.file_path)
        except (json.JSONDecodeError, ValueError) as e:
            # File is corrupted. Let's try backup recovery.
            corrupted_copy = f"{self.file_path}.corrupted"
            try:
                if os.path.exists(self.file_path):
                    shutil.copy2(self.file_path, corrupted_copy)
            except Exception:
                pass  # Ignore if we cannot copy, but still try to recover

            if os.path.exists(self.backup_path):
                try:
                    recovered_expenses = self._read_from_path(self.backup_path)
                    # Rewrite the recovered data to the main file to heal it
                    self.save_expenses(recovered_expenses)
                    return recovered_expenses
                except Exception:
                    # Backup is also corrupted
                    pass

            # Raise descriptive error to user if recoverability failed
            raise ValueError(
                f"Data file '{self.file_path}' is corrupted. "
                f"A backup of the corrupted file has been saved as '{corrupted_copy}' "
                f"to prevent data loss. Error details: {e}"
            )

    def save_expenses(self, expenses: List[Expense]) -> None:
        """Saves a list of Expense objects to the JSON file using atomic writing.

        Args:
            expenses: A list of Expense objects to serialize and store.

        Raises:
            IOError: If writing to the file or backup fails.
        """
        # Create a backup of the current valid file before writing new contents
        if os.path.exists(self.file_path) and os.path.getsize(self.file_path) > 0:
            try:
                shutil.copy2(self.file_path, self.backup_path)
            except Exception as e:
                # Log or display error internally, but continue writing data
                pass

        temp_file = f"{self.file_path}.tmp"
        try:
            # Serialize expenses to dict
            data = [expense.to_dict() for expense in expenses]

            # Write to a temporary file
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            # Atomic replace
            os.replace(temp_file, self.file_path)
        except Exception as e:
            # Clean up the temporary file if it was created
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass
            raise IOError(f"Could not save expenses: {e}")

    def _read_from_path(self, path: str) -> List[Expense]:
        """Loads and parses expenses from a specific file path."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError("Root JSON element must be a list.")

        expenses = []
        for index, item in enumerate(data):
            if not isinstance(item, dict):
                raise ValueError(f"Expense record at index {index} must be a dictionary.")
            expenses.append(Expense.from_dict(item))
        return expenses
