from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any, Dict


class Expense:
    """Represents a single personal expense with validation and serialization capability."""

    def __init__(
        self,
        title: str,
        amount: float,
        category: str,
        date: str,
        id: str | None = None,
        created_at: str | None = None,
    ) -> None:
        """Initializes an Expense object.

        Args:
            title: The title/description of the expense.
            amount: The cost of the expense (must be greater than 0).
            category: The category classification of the expense.
            date: The date when the expense occurred (YYYY-MM-DD).
            id: Unique identifier. Generates a new UUID hex string if not provided.
            created_at: ISO-formatted timestamp. Defaults to current date/time if not provided.

        Raises:
            ValueError: If any validation checks fail.
        """
        # Set immutable/internal fields first
        self.id: str = id if id else uuid.uuid4().hex
        self.created_at: str = created_at if created_at else datetime.now().isoformat()

        # Set attributes using properties to trigger validation
        self.title = title
        self.amount = amount
        self.category = category
        self.date = date

    @property
    def title(self) -> str:
        """Gets the expense title."""
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        """Sets the expense title. Raises ValueError if empty or whitespace-only."""
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Expense title cannot be empty.")
        self._title = value.strip()

    @property
    def amount(self) -> float:
        """Gets the expense amount."""
        return self._amount

    @amount.setter
    def amount(self, value: float) -> None:
        """Sets the expense amount. Raises ValueError if not a positive float."""
        try:
            val = float(value)
        except (ValueError, TypeError):
            raise ValueError("Expense amount must be a numeric value.")

        if val <= 0:
            raise ValueError("Expense amount must be greater than zero.")
        self._amount = val

    @property
    def category(self) -> str:
        """Gets the expense category."""
        return self._category

    @category.setter
    def category(self, value: str) -> None:
        """Sets the expense category. Raises ValueError if empty or whitespace-only."""
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Expense category cannot be empty.")
        self._category = value.strip()

    @property
    def date(self) -> str:
        """Gets the expense date in YYYY-MM-DD format."""
        return self._date

    @date.setter
    def date(self, value: str) -> None:
        """Sets the expense date. Validates YYYY-MM-DD format."""
        if not isinstance(value, str):
            raise ValueError("Expense date must be a string.")
        
        date_str = value.strip()
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date format '{value}'. Date must be in YYYY-MM-DD format.")
        self._date = date_str

    def to_dict(self) -> Dict[str, Any]:
        """Converts the Expense object to a dictionary representation for serialization.

        Returns:
            A dictionary containing all the expense attributes.
        """
        return {
            "id": self.id,
            "title": self.title,
            "amount": self.amount,
            "category": self.category,
            "date": self.date,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Expense":
        """Creates an Expense instance from a dictionary.

        Args:
            data: A dictionary containing key-value pairs representing an Expense.

        Returns:
            An Expense object.

        Raises:
            ValueError: If required fields are missing.
        """
        required_keys = {"id", "title", "amount", "category", "date", "created_at"}
        if not required_keys.issubset(data.keys()):
            missing = required_keys - data.keys()
            raise ValueError(f"Invalid expense data. Missing fields: {missing}")

        return cls(
            id=data["id"],
            title=data["title"],
            amount=data["amount"],
            category=data["category"],
            date=data["date"],
            created_at=data["created_at"],
        )

    def __repr__(self) -> str:
        """Returns string representation of Expense for debugging."""
        return (
            f"Expense(id='{self.id}', title='{self.title}', amount={self.amount}, "
            f"category='{self.category}', date='{self.date}')"
        )
