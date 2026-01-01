"""Utility functions for the bot."""


def calculate_accuracy(guessed: float, actual: float) -> float:
    """
    Calculate accuracy percentage between guessed and actual amounts.

    Args:
        guessed: The guessed amount
        actual: The actual amount

    Returns:
        Accuracy percentage, clamped between -100 and 100.
        Returns 0% if both are zero, -100% if actual is zero but guessed is not.
    """
    if actual == 0:
        return 0.0 if guessed == 0 else -100.0

    accuracy = 100 - abs((guessed - actual) / actual * 100)
    return max(-100.0, min(100.0, accuracy))
