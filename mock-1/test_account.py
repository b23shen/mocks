"""Tests for the Account class in account.py. All money values are int cents."""

import pytest

from account import Account
from errors import InsufficientFundsError, InvalidAccountIdError, InvalidAmountError


def test_new_account_starts_with_zero_balance() -> None:
    """A new account with no starting balance has 0 cents."""
    account = Account("acc-1")
    assert account.get_balance() == 0


def test_deposit_increases_balance() -> None:
    """Deposits add cents to the balance."""
    account = Account("acc-1")
    assert account.deposit(1025) == 1025
    assert account.deposit(500) == 1525
    assert account.get_balance() == 1525


def test_withdraw_decreases_balance() -> None:
    """A withdrawal subtracts cents from the balance."""
    account = Account("acc-1", 2050)
    assert account.withdraw(525) == 1525
    assert account.get_balance() == 1525


def test_withdraw_full_balance_leaves_zero() -> None:
    """Withdrawing the exact balance is allowed and leaves 0."""
    account = Account("acc-1", 1234)
    assert account.withdraw(1234) == 0


def test_withdraw_more_than_balance_raises_and_keeps_balance() -> None:
    """Overdrawing by even 1 cent raises and leaves the balance unchanged."""
    account = Account("acc-1", 1000)
    with pytest.raises(InsufficientFundsError):
        account.withdraw(1001)
    assert account.get_balance() == 1000


@pytest.mark.parametrize("amount", [0, -5])
@pytest.mark.parametrize("action", ["deposit", "withdraw"])
def test_zero_or_negative_amount_raises(action: str, amount: int) -> None:
    """Amounts that are not > 0 are rejected and the balance does not change."""
    account = Account("acc-1", 1000)
    with pytest.raises(InvalidAmountError):
        getattr(account, action)(amount)
    assert account.get_balance() == 1000


@pytest.mark.parametrize("amount", ["1000", True, None, 10.5, 10.0])
@pytest.mark.parametrize("action", ["deposit", "withdraw"])
def test_invalid_type_amount_raises_type_error(action: str, amount: object) -> None:
    """Non-int amounts raise TypeError, including bool and whole-number floats."""
    account = Account("acc-1", 1000)
    with pytest.raises(TypeError):
        getattr(account, action)(amount)
    assert account.get_balance() == 1000


@pytest.mark.parametrize(
    ("account_id", "balance", "error"),
    [
        ("", 0, InvalidAccountIdError),
        ("   ", 0, InvalidAccountIdError),
        (123, 0, TypeError),
        ("acc-1", -1, InvalidAmountError),
        ("acc-1", 10.0, TypeError),
    ],
)
def test_invalid_account_setup_raises(
    account_id: object, balance: object, error: type[Exception]
) -> None:
    """Bad ids and bad starting balances are rejected when creating an account."""
    with pytest.raises(error):
        Account(account_id, balance)  # type: ignore[arg-type]
