"""Budget data storage using JSON files."""

import json
from pathlib import Path
from datetime import datetime
from bot.models import BudgetEntry, MonthlyBudget


class BudgetStorage:
    """Handle budget data persistence."""

    def __init__(self, data_dir: str = "data"):
        """Initialize budget storage.

        Args:
            data_dir: Base data directory
        """
        self.data_dir = Path(data_dir)
        self.budget_dir = self.data_dir / "budgets"
        self.budget_dir.mkdir(parents=True, exist_ok=True)

    def save_entry(self, entry: BudgetEntry) -> str:
        """Save a budget entry to JSON file.

        Args:
            entry: BudgetEntry to save

        Returns:
            Filename of saved entry
        """
        month_dir = self.budget_dir / entry.month
        month_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{entry.date:%Y-%m-%d_%H%M}_{entry.id}.json"
        filepath = month_dir / filename

        with open(filepath, "w") as f:
            json.dump(entry.model_dump(), f, indent=2, default=str)

        return filename

    def load_month_entries(self, month: str) -> list[BudgetEntry]:
        """Load all budget entries for a specific month.

        Args:
            month: Month in YYYY-MM format

        Returns:
            List of BudgetEntry objects sorted by date
        """
        month_dir = self.budget_dir / month
        if not month_dir.exists():
            return []

        entries = []
        for filepath in month_dir.glob("*.json"):
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    # Convert string dates back to datetime
                    data['date'] = datetime.fromisoformat(data['date'])
                    data['created_at'] = datetime.fromisoformat(data['created_at'])
                    entries.append(BudgetEntry(**data))
            except Exception as e:
                print(f"Error loading {filepath}: {e}")

        return sorted(entries, key=lambda x: x.date)

    def get_monthly_budget(self, month: str, budget_limit: float = 100.0) -> MonthlyBudget:
        """Get monthly budget summary.

        Args:
            month: Month in YYYY-MM format
            budget_limit: Monthly budget limit (default: $100)

        Returns:
            MonthlyBudget object with calculated values
        """
        entries = self.load_month_entries(month)
        spent = sum(entry.amount for entry in entries)
        remaining = budget_limit - spent
        overspent = spent > budget_limit
        surplus = max(0, remaining)  # Only positive surplus counts

        return MonthlyBudget(
            month=month,
            budget_limit=budget_limit,
            spent=spent,
            remaining=remaining,
            entries=entries,
            overspent=overspent,
            surplus=surplus
        )

    def get_year_surplus(self, year: int = 2026) -> float:
        """Calculate total surplus for the year (excluding Nov/Dec).

        Args:
            year: Year to calculate

        Returns:
            Total surplus amount
        """
        total_surplus = 0.0

        # Calculate surplus from Jan to Oct (months 1-10)
        for month_num in range(1, 11):
            month = f"{year}-{month_num:02d}"
            budget = self.get_monthly_budget(month)
            if not budget.overspent:
                total_surplus += budget.surplus

        return total_surplus
