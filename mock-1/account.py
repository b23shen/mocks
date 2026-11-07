"""A simple bank account that supports deposit, withdraw, and balance checks.

All money values are whole cents stored as int (for example, 1234 means
12 dollars and 34 cents). Using int cents keeps all math exact, so there
are no floating point rounding errors.
"""


class InvalidAmountError(ValueError):
    """Raised when an amount of cents is not a valid value."""


class InsufficientFundsError(ValueError):
    """Raised when a withdrawal is larger than the current balance."""


def _validate_cents(value: int, name: str) -> int:
    """Check that a value is an int number of cents.

    Args:
        value: The value to check.
        name: The name of the value, used in error messages.

    Returns:
        The value, unchanged.

    Raises:
        TypeError: If value is not an int, or if it is a bool.
    """
    # bool is a subclass of int, but True/False are never real money.
    # float is rejected so callers cannot pass dollars (10.25) by mistake.
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an int number of cents, got {type(value).__name__}")
    return value


def _validate_amount(amount: int) -> int:
    """Check that an amount of cents for deposit or withdraw is valid.

    Args:
        amount: The amount in cents to check.

    Returns:
        The amount, unchanged.

    Raises:
        TypeError: If amount is not an int, or if it is a bool.
        InvalidAmountError: If amount is not greater than 0.
    """
    value = _validate_cents(amount, "amount")
    if value <= 0:
        raise InvalidAmountError(f"amount must be greater than 0, got {amount}")
    return value


class Account:
    """A bank account with an id and a balance in cents that never goes below 0.

    Attributes:
        account_id: The unique id of the account.
    """

    def __init__(self, account_id: str, balance: int = 0) -> None:
        """Create an account.

        Args:
            account_id: The id of the account. Must be a non-empty string.
            balance: The starting balance in cents. Must be >= 0.
                Defaults to 0.

        Raises:
            TypeError: If account_id is not a str, or balance is not an int
                (or is a bool).
            ValueError: If account_id is empty or only whitespace.
            InvalidAmountError: If balance is negative.
        """
        if not isinstance(account_id, str):
            raise TypeError(f"account_id must be a str, got {type(account_id).__name__}")
        if not account_id.strip():
            raise ValueError("account_id must not be empty")
        start = _validate_cents(balance, "balance")
        if start < 0:
            raise InvalidAmountError(f"balance must be >= 0, got {balance}")

        self.account_id = account_id
        self._balance = start

    def deposit(self, amount: int) -> int:
        """Add money to the account.

        Args:
            amount: The cents to add. Must be > 0.

        Returns:
            The new balance in cents.

        Raises:
            TypeError: If amount is not an int, or if it is a bool.
            InvalidAmountError: If amount is not > 0.
        """
        value = _validate_amount(amount)
        self._balance += value
        return self._balance

    def withdraw(self, amount: int) -> int:
        """Take money out of the account.

        The balance does not change if the withdrawal fails.

        Args:
            amount: The cents to take out. Must be > 0.

        Returns:
            The new balance in cents.

        Raises:
            TypeError: If amount is not an int, or if it is a bool.
            InvalidAmountError: If amount is not > 0.
            InsufficientFundsError: If amount is larger than the balance.
        """
        value = _validate_amount(amount)
        if value > self._balance:
            raise InsufficientFundsError(
                f"cannot withdraw {value} cents, balance is only {self._balance} cents"
            )
        self._balance -= value
        return self._balance

    def get_balance(self) -> int:
        """Return the current balance.

        Returns:
            The current balance in cents.
        """
        return self._balance
