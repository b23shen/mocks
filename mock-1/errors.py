"""All custom errors for the account and bank modules.

Every error is a subclass of BankError, so callers can catch all of them
with one `except BankError`. Errors about bad input values are also
subclasses of ValueError, and the "not found" error is also a LookupError,
so code that catches those built-in errors keeps working.
"""


class BankError(Exception):
    """Base class for all errors raised by the account and bank modules."""


class InvalidAmountError(BankError, ValueError):
    """Raised when an amount of cents is not a valid value."""


class InvalidAccountIdError(BankError, ValueError):
    """Raised when an account id is empty or only whitespace."""


class DuplicateAccountError(BankError, ValueError):
    """Raised when an account id is already used in the bank."""


class SameAccountTransferError(BankError, ValueError):
    """Raised when a transfer uses the same account as source and target."""


class AccountNotFoundError(BankError, LookupError):
    """Raised when no account has the given id."""


class InsufficientFundsError(BankError):
    """Raised when a withdrawal is larger than the current balance.

    This is not a ValueError: the amount itself is valid, but the account
    does not have enough money.
    """
