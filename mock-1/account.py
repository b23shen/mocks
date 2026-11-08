"""A simple bank account with deposit, withdraw, balance, and history.

All money values are whole cents stored as int (for example, 1234 means
12 dollars and 34 cents). Using int cents keeps all math exact, so there
are no floating point rounding errors.
"""

from errors import InsufficientFundsError, InvalidAccountIdError, InvalidAmountError
from transaction import Transaction, TransactionKind


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
    """A bank account with an id, a balance in cents, and a transaction history.

    The balance never goes below 0. Every successful balance change adds one
    Transaction to the history; failed actions add nothing.

    Attributes:
        account_id: The unique id of the account.
    """

    def __init__(self, account_id: str, balance: int = 0) -> None:
        """Create an account.

        If the starting balance is > 0, the history starts with one OPENING
        transaction, so the history explains the full balance.

        Args:
            account_id: The id of the account. Must be a non-empty string.
            balance: The starting balance in cents. Must be >= 0.
                Defaults to 0.

        Raises:
            TypeError: If account_id is not a str, or balance is not an int
                (or is a bool).
            InvalidAccountIdError: If account_id is empty or only whitespace.
            InvalidAmountError: If balance is negative.
        """
        if not isinstance(account_id, str):
            raise TypeError(f"account_id must be a str, got {type(account_id).__name__}")
        if not account_id.strip():
            raise InvalidAccountIdError("account_id must not be empty")
        start = _validate_cents(balance, "balance")
        if start < 0:
            raise InvalidAmountError(f"balance must be >= 0, got {balance}")

        self.account_id = account_id
        self._balance = start
        self._history: list[Transaction] = []
        if start > 0:
            self._history.append(Transaction(TransactionKind.OPENING, start, start))

    def deposit(self, amount: int) -> int:
        """Add money to the account and record a DEPOSIT.

        Args:
            amount: The cents to add. Must be > 0.

        Returns:
            The new balance in cents.

        Raises:
            TypeError: If amount is not an int, or if it is a bool.
            InvalidAmountError: If amount is not > 0.
        """
        return self._add_money(amount, TransactionKind.DEPOSIT, None)

    def withdraw(self, amount: int) -> int:
        """Take money out of the account and record a WITHDRAWAL.

        The balance and history do not change if the withdrawal fails.

        Args:
            amount: The cents to take out. Must be > 0.

        Returns:
            The new balance in cents.

        Raises:
            TypeError: If amount is not an int, or if it is a bool.
            InvalidAmountError: If amount is not > 0.
            InsufficientFundsError: If amount is larger than the balance.
        """
        return self._remove_money(amount, TransactionKind.WITHDRAWAL, None)

    def transfer_in(self, amount: int, from_account_id: str) -> int:
        """Add money that comes from another account and record a TRANSFER_IN.

        Used by Bank.transfer. It does not check that from_account_id exists.

        Args:
            amount: The cents to add. Must be > 0.
            from_account_id: The id of the account the money came from.

        Returns:
            The new balance in cents.

        Raises:
            TypeError: If amount is not an int, or if it is a bool.
            InvalidAmountError: If amount is not > 0.
        """
        return self._add_money(amount, TransactionKind.TRANSFER_IN, from_account_id)

    def transfer_out(self, amount: int, to_account_id: str) -> int:
        """Take money out for another account and record a TRANSFER_OUT.

        Used by Bank.transfer. It does not check that to_account_id exists.
        The balance and history do not change if this fails.

        Args:
            amount: The cents to take out. Must be > 0.
            to_account_id: The id of the account the money goes to.

        Returns:
            The new balance in cents.

        Raises:
            TypeError: If amount is not an int, or if it is a bool.
            InvalidAmountError: If amount is not > 0.
            InsufficientFundsError: If amount is larger than the balance.
        """
        return self._remove_money(amount, TransactionKind.TRANSFER_OUT, to_account_id)

    def get_balance(self) -> int:
        """Return the current balance.

        Returns:
            The current balance in cents.
        """
        return self._balance

    def get_history(self) -> tuple[Transaction, ...]:
        """Return all transactions on this account, oldest first.

        Returns:
            A tuple of transactions. It is a copy, so callers cannot change
            the account's real history.
        """
        return tuple(self._history)

    def _add_money(
        self, amount: int, kind: TransactionKind, related_account_id: str | None
    ) -> int:
        """Check an amount, add it to the balance, and record it.

        Args:
            amount: The cents to add. Must be > 0.
            kind: The transaction kind to record.
            related_account_id: The other account's id for a transfer, else None.

        Returns:
            The new balance in cents.

        Raises:
            TypeError: If amount is not an int, or if it is a bool.
            InvalidAmountError: If amount is not > 0.
        """
        value = _validate_amount(amount)
        self._balance += value
        self._record(kind, value, related_account_id)
        return self._balance

    def _remove_money(
        self, amount: int, kind: TransactionKind, related_account_id: str | None
    ) -> int:
        """Check an amount, subtract it from the balance, and record it.

        Args:
            amount: The cents to take out. Must be > 0.
            kind: The transaction kind to record.
            related_account_id: The other account's id for a transfer, else None.

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
        self._record(kind, value, related_account_id)
        return self._balance

    def _record(
        self, kind: TransactionKind, amount: int, related_account_id: str | None
    ) -> None:
        """Add one transaction to the history, using the current balance.

        Call this only after the balance has changed, so balance_after is right.

        Args:
            kind: The transaction kind.
            amount: The cents moved.
            related_account_id: The other account's id for a transfer, else None.
        """
        self._history.append(
            Transaction(kind, amount, self._balance, related_account_id)
        )
