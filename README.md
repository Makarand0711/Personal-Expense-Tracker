# Personal Expense Tracker

A modular, robust, and beginner-friendly command-line interface (CLI) application built in Python to help users manage, view, and analyze their daily expenses. This project showcases standard software design principles (Separation of Concerns), Python fundamentals, object-oriented programming, data validation, automated unit testing, and safe file persistence.

---

## Features

### 🌟 Core Features
- **Add Expense**: Interactive prompts to add a title, amount, category, and date (defaults to today's date). Re-prompts on invalid formats automatically.
- **View Expenses**: Formatted, color-coded tabular output featuring alternating colors for row readability.
- **Search Expense**: Case-insensitive search by Title, Category, or Date (allows partial matches, e.g. finding `"2026-06"` matches all records of June 2026).
- **Update Expense**: Update any field by specifying an expense ID. Pressing `Enter` keeps the current value.
- **Delete Expense**: Safely remove records by ID with an explicit confirmation step.
- **Monthly Summary**: Calculate total spend, average spend, count of transactions, the highest expense details, and a sorted breakdown of categories for any specified Month/Year.
- **Statistics**: Display overall stats, the most frequent spending category, and chronological monthly spending history featuring an interactive ASCII bar chart.

### 🚀 Bonus Features Included
- **Dynamic Prefix-Matching for IDs**: You do not need to copy and paste the entire 32-character UUID; you can type the first few characters (e.g. the first 4 or 8 digits) and the application will match it, asking for clarification if there is a collision.
- **Interactive Pagination**: View large expense tables 10 records at a time using `[N] Next` and `[P] Previous` console navigation.
- **Multi-key Sorting**: Dynamically sort records in ascending or descending order by Date, Amount, Title, or Category.
- **CSV Data Utilities**: Export your expense history to CSV or import CSV data files with automated row-by-row structure validation and collision resolution.
- **Robust Persistence & Anti-Corruption**: Uses atomic file writing via temporary files to avoid partial write failures. Keeps automatic `.bak` backups and copies corrupted files to `.corrupted` safely without losing data.

---

## Folder Structure

```text
ExpenseTracker/
│
├── main.py                     # CLI Interactive Loop & Inputs Validation
├── expense_manager.py          # CRUD Operations, CSV utilities, Sorting, & Statistics
├── models.py                   # Expense Class representation, Getters/Setters, & validations
├── storage.py                  # JSON Load/Save handler with Atomic Writes & Backup/Recovery
├── expenses.json               # Data storage file (automatically generated)
├── requirements.txt            # Project dependencies (colorama)
├── README.md                   # Documentation guide
└── tests/
    └── test_expense_manager.py # Unit tests covering core functions and recovery
