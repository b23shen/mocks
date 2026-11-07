"""A bank that holds many accounts and runs actions on them by account id.

All money values are int cents, the same as in account.py. Amount checks
are done by Account, so the bank does not repeat them.
"""

from collections.abc import Iterable

from account import Account
from errors import AccountNotFoundError, DuplicateAccountError


class Bank:
    """A collection of accounts, each found by its exact account id."""

    def __init__(self, accounts: Iterable[Account] | None = None) -> None:
        """Create a bank, optionally with existing accounts.

        The bank keeps the given Account objects themselves (not copies).

        Args:
            accounts: Accounts to start with. Defaults to no accounts.

        Raises:
            TypeError: If any item in accounts is not an Account.
            DuplicateAccountError: If two accounts have the same id.
        """
        self._accounts: dict[str, Account] = {}
        for account in accounts or []:
            self._add(account)

    def open_account(self, account_id: str, balance: int = 0) -> Account:
        """Open a new account and add it to the bank.

        Args:
            account_id: The id of the new account. Must be a non-empty string
                that is not already used in the bank.
            balance: The starting balance in cents. Must be >= 0.
                Defaults to 0.

        Returns:
            The new account.

        Raises:
            TypeError: If account_id is not a str, or balance is not an int.
            InvalidAccountIdError: If account_id is empty or only whitespace.
            InvalidAmountError: If balance is negative.
            DuplicateAccountError: If account_id is already used.
        """
        # Account checks the id and balance first; _add then checks for a
        # duplicate id. A rejected Account is never stored.
        account = Account(account_id, balance)
        self._add(account)
        return account

    def get_account(self, account_id: str) -> Account:
        """Find an account by its id.

        Args:
            account_id: The exact id of the account.

        Returns:
            The account with that id.

        Raises:
            TypeError: If account_id is not a str.
            AccountNotFoundError: If no account has that id.
        """
        if not isinstance(account_id, str):
            raise TypeError(f"account_id must be a str, got {type(account_id).__name__}")
        try:
            return self._accounts[account_id]
        except KeyError:
            raise AccountNotFoundError(f"account {account_id!r} not found") from None

    def transfer(self, account_out: str, account_in: str, amount: int) -> None:
        "transfer money amount from account_out to account_in"
        # should check balance first and then perform action
        self.withdraw(account_out, amount) # withdraw will be blocked if no account_out or amount is larger than balance
        try: 
            self.deposit(account_in, amount)
        except:
            # one more edge cases: withdraw succceed but deposit didn't, it needs the money back to account_out
            self.deposit(account_out, amount)
            raise AccountNotFoundError(f"account {account_out!r} not found")

    def deposit(self, account_id: str, amount: int) -> int:
        """Add money to an account.

        Args:
            account_id: The exact id of the account.
            amount: The cents to add. Must be > 0.

        Returns:
            The new balance of the account in cents.

        Raises:
            TypeError: If account_id is not a str, or amount is not an int.
            AccountNotFoundError: If no account has that id.
            InvalidAmountError: If amount is not > 0.
        """
        return self.get_account(account_id).deposit(amount)

    def withdraw(self, account_id: str, amount: int) -> int:
        """Take money out of an account.

        Args:
            account_id: The exact id of the account.
            amount: The cents to take out. Must be > 0.

        Returns:
            The new balance of the account in cents.

        Raises:
            TypeError: If account_id is not a str, or amount is not an int.
            AccountNotFoundError: If no account has that id.
            InvalidAmountError: If amount is not > 0.
            InsufficientFundsError: If amount is larger than the balance.
        """
        return self.get_account(account_id).withdraw(amount)

    def _add(self, account: Account) -> None:
        """Add an existing Account object to the bank.

        Args:
            account: The account to add.

        Raises:
            TypeError: If account is not an Account.
            DuplicateAccountError: If its id is already used.
        """
        if not isinstance(account, Account):
            raise TypeError(f"expected an Account, got {type(account).__name__}")
        if account.account_id in self._accounts:
            raise DuplicateAccountError(f"account {account.account_id!r} already exists")
        self._accounts[account.account_id] = account
