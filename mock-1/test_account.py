"""Tests for the Account class in account.py."""

import math

import pytest

from account import Account, InsufficientFundsError, InvalidAmountError


def test_new_account_starts_with_zero_balance() -> None:
    """A new account with no starting balance has 0.0."""
    account = Account("acc-1")
    assert account.get_balance() == 0.0


def test_deposit_increases_balance() -> None:
    """Deposits add to the balance, including cents."""
    account = Account("acc-1")
    assert account.deposit(10.25) == 10.25
    assert account.deposit(5) == 15.25
    assert account.get_balance() == 15.25


def test_withdraw_decreases_balance() -> None:
    """A withdrawal subtracts from the balance."""
    account = Account("acc-1", 20.50)
    assert account.withdraw(5.25) == 15.25
    assert account.get_balance() == 15.25


def test_withdraw_full_balance_leaves_zero() -> None:
    """Withdrawing the exact balance is allowed and leaves 0."""
    account = Account("acc-1", 12.34)
    assert account.withdraw(12.34) == 0.0


def test_withdraw_more_than_balance_raises_and_keeps_balance() -> None:
    """Overdrawing raises InsufficientFundsError and leaves the balance unchanged."""
    account = Account("acc-1", 10.00)
    with pytest.raises(InsufficientFundsError):
        account.withdraw(10.01)
    assert account.get_balance() == 10.00


@pytest.mark.parametrize("amount", [0, 0.0, -5, -0.01])
@pytest.mark.parametrize("action", ["deposit", "withdraw"])
def test_zero_or_negative_amount_raises(action: str, amount: float) -> None:
    """Amounts that are not > 0 are rejected and the balance does not change."""
    account = Account("acc-1", 10.00)
    with pytest.raises(InvalidAmountError):
        getattr(account, action)(amount)
    assert account.get_balance() == 10.00


@pytest.mark.parametrize("amount", ["10", True, None])
@pytest.mark.parametrize("action", ["deposit", "withdraw"])
def test_invalid_type_amount_raises_type_error(action: str, amount: object) -> None:
    """Non-number amounts (and bool) raise TypeError."""
    account = Account("acc-1", 10.00)
    with pytest.raises(TypeError):
        getattr(account, action)(amount)
    assert account.get_balance() == 10.00


@pytest.mark.parametrize("amount", [1.005, math.nan, math.inf])
def test_bad_float_amount_raises(amount: float) -> None:
    """Floats with too many decimals, NaN, or infinity are rejected.

    Also checks that repeated 0.1 withdrawals end at exactly 0, so float
    rounding errors do not block a valid withdrawal.
    """
    account = Account("acc-1", 0.3)
    with pytest.raises(InvalidAmountError):
        account.deposit(amount)
    with pytest.raises(InvalidAmountError):
        account.withdraw(amount)

    for _ in range(3):
        account.withdraw(0.1)
    assert account.get_balance() == 0.0
