"""A simple bank account that supports deposit, withdraw, and balance checks.

Money is stored as a float in currency units (for example, 12.34 means
12 dollars and 34 cents). Amounts may have at most 2 decimal places.
"""

import math

# Money has cents, so 2 decimal places is the smallest valid unit.
_CENT_DECIMALS = 2


class InvalidAmountError(ValueError):
    """Raised when an amount is not a valid positive money value."""


class InsufficientFundsError(ValueError):
    """Raised when a withdrawal is larger than the current balance."""


def _validate_number(value: float, name: str) -> float:
    """Check that a value is a finite number with at most 2 decimal places.

    Args:
        value: The value to check.
        name: The name of the value, used in error messages.

    Returns:
        The value as a float.

    Raises:
        TypeError: If value is not an int or float, or if it is a bool.
        InvalidAmountError: If value is NaN, infinite, or has more than
            2 decimal places.
    """
    # bool is a subclass of int, but True/False are never real money.
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a number, got {type(value).__name__}")
    if not math.isfinite(value):
        raise InvalidAmountError(f"{name} must be a finite number, got {value}")
    if round(value, _CENT_DECIMALS) != value:
        raise InvalidAmountError(f"{name} must have at most 2 decimal places, got {value}")
    return float(value)


def _validate_amount(amount: float) -> float:
    """Check that an amount for deposit or withdraw is valid.

    Args:
        amount: The money amount to check.

    Returns:
        The amount as a float.

    Raises:
        TypeError: If amount is not an int or float, or if it is a bool.
        InvalidAmountError: If amount is not greater than 0, is not finite,
            or has more than 2 decimal places.
    """
    value = _validate_number(amount, "amount")
    if value <= 0:
        raise InvalidAmountError(f"amount must be greater than 0, got {amount}")
    return value


class Account:
    """A bank account with an id and a balance that never goes below 0.

    Attributes:
        account_id: The unique id of the account.
    """

    def __init__(self, account_id: str, balance: float = 0.0) -> None:
        """Create an account.

        Args:
            account_id: The id of the account. Must be a non-empty string.
            balance: The starting balance. Must be >= 0 with at most
                2 decimal places. Defaults to 0.0.

        Raises:
            TypeError: If account_id is not a str, or balance is not a number.
            ValueError: If account_id is empty or only whitespace.
            InvalidAmountError: If balance is negative, not finite, or has
                more than 2 decimal places.
        """
        if not isinstance(account_id, str):
            raise TypeError(f"account_id must be a str, got {type(account_id).__name__}")
        if not account_id.strip():
            raise ValueError("account_id must not be empty")
        start = _validate_number(balance, "balance")
        if start < 0:
            raise InvalidAmountError(f"balance must be >= 0, got {balance}")

        self.account_id = account_id
        self._balance = start

    def deposit(self, amount: float) -> float:
        """Add money to the account.

        Args:
            amount: The money to add. Must be > 0 with at most 2 decimal places.

        Returns:
            The new balance.

        Raises:
            TypeError: If amount is not an int or float, or if it is a bool.
            InvalidAmountError: If amount is not > 0, is not finite, or has
                more than 2 decimal places.
        """
        value = _validate_amount(amount)
        self._balance = self._round_cents(self._balance + value)
        return self._balance

    def withdraw(self, amount: float) -> float:
        """Take money out of the account.

        The balance does not change if the withdrawal fails.

        Args:
            amount: The money to take out. Must be > 0 with at most
                2 decimal places.

        Returns:
            The new balance.

        Raises:
            TypeError: If amount is not an int or float, or if it is a bool.
            InvalidAmountError: If amount is not > 0, is not finite, or has
                more than 2 decimal places.
            InsufficientFundsError: If amount is larger than the balance.
        """
        value = _validate_amount(amount)
        if value > self._balance:
            raise InsufficientFundsError(
                f"cannot withdraw {value:.2f}, balance is only {self._balance:.2f}"
            )
        self._balance = self._round_cents(self._balance - value)
        return self._balance

    def get_balance(self) -> float:
        """Return the current balance.

        Returns:
            The current balance, rounded to cents.
        """
        return self._balance

    @staticmethod
    def _round_cents(value: float) -> float:
        """Round a value to whole cents.

        Float math is not exact (for example, 0.3 - 0.1 - 0.1 gives
        0.09999999999999998). Rounding after every change stops these small
        errors from adding up and blocking a valid withdrawal.

        Args:
            value: The value to round.

        Returns:
            The value rounded to 2 decimal places.
        """
        return round(value, _CENT_DECIMALS)
