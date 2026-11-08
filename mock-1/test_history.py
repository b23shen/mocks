"""Tests for transaction history on Account and Bank. All money is int cents."""

import dataclasses

import pytest

from account import Account
from bank import Bank
from errors import (
    AccountNotFoundError,
    InsufficientFundsError,
    InvalidAmountError,
    SameAccountTransferError,
)
from transaction import Transaction, TransactionKind


@pytest.fixture
def bank() -> Bank:
    """Return a bank with two accounts: a1 opened with 1000 cents, a2 with 0."""
    return Bank([Account("a1", 1000), Account("a2")])


def test_new_account_with_zero_balance_has_empty_history() -> None:
    """An account opened with 0 cents has no transactions."""
    assert Account("acc-1").get_history() == ()


def test_starting_balance_adds_opening_record(bank: Bank) -> None:
    """A starting balance > 0 is recorded as one OPENING transaction."""
    assert bank.get_history("a1") == (Transaction(TransactionKind.OPENING, 1000, 1000),)
    opened = bank.open_account("a3", 250)
    assert opened.get_history() == (Transaction(TransactionKind.OPENING, 250, 250),)


def test_deposit_and_withdraw_recorded_in_order_with_balance_after(bank: Bank) -> None:
    """Each action adds one record, oldest first, with the balance after it."""
    bank.deposit("a1", 250)
    bank.withdraw("a1", 50)
    bank.deposit("a1", 1)
    assert bank.get_history("a1") == (
        Transaction(TransactionKind.OPENING, 1000, 1000),
        Transaction(TransactionKind.DEPOSIT, 250, 1250),
        Transaction(TransactionKind.WITHDRAWAL, 50, 1200),
        Transaction(TransactionKind.DEPOSIT, 1, 1201),
    )


def test_transfer_records_on_both_accounts(bank: Bank) -> None:
    """A transfer adds TRANSFER_OUT and TRANSFER_IN, each naming the other account."""
    bank.transfer("a1", "a2", 300)
    assert bank.get_history("a1")[-1] == Transaction(
        TransactionKind.TRANSFER_OUT, 300, 700, related_account_id="a2"
    )
    assert bank.get_history("a2") == (
        Transaction(TransactionKind.TRANSFER_IN, 300, 300, related_account_id="a1"),
    )


@pytest.mark.parametrize(
    ("action", "amount", "error"),
    [
        ("deposit", 0, InvalidAmountError),
        ("withdraw", -5, InvalidAmountError),
        ("withdraw", 1001, InsufficientFundsError),
        ("deposit", 10.5, TypeError),
    ],
)
def test_failed_actions_add_no_history(
    bank: Bank, action: str, amount: object, error: type[Exception]
) -> None:
    """A failed deposit or withdraw leaves the history unchanged."""
    before = bank.get_history("a1")
    with pytest.raises(error):
        getattr(bank, action)("a1", amount)
    assert bank.get_history("a1") == before


@pytest.mark.parametrize(
    ("account_out", "account_in", "amount", "error"),
    [
        ("a1", "missing", 100, AccountNotFoundError),
        ("missing", "a2", 100, AccountNotFoundError),
        ("a1", "a2", 1001, InsufficientFundsError),
        ("a1", "a2", 0, InvalidAmountError),
        ("a1", "a1", 100, SameAccountTransferError),
    ],
    ids=["unknown-target", "unknown-source", "overdraw", "zero-amount", "same-account"],
)
def test_failed_transfer_adds_no_history_to_either_account(
    bank: Bank, account_out: str, account_in: str, amount: int, error: type[Exception]
) -> None:
    """A failed transfer changes neither account's history or balance."""
    before_a1 = bank.get_history("a1")
    before_a2 = bank.get_history("a2")
    with pytest.raises(error):
        bank.transfer(account_out, account_in, amount)
    assert bank.get_history("a1") == before_a1
    assert bank.get_history("a2") == before_a2
    assert bank.get_account("a1").get_balance() == 1000
    assert bank.get_account("a2").get_balance() == 0


def test_history_cannot_be_changed_by_caller(bank: Bank) -> None:
    """The returned history is a tuple copy, and each record is frozen."""
    history = bank.get_history("a1")
    assert isinstance(history, tuple)

    # Changing a list made from the copy must not touch the real history.
    as_list = list(history)
    as_list.append(Transaction(TransactionKind.DEPOSIT, 5, 5))
    assert len(bank.get_history("a1")) == 1

    with pytest.raises(dataclasses.FrozenInstanceError):
        history[0].amount = 999  # type: ignore[misc]


@pytest.mark.parametrize("account_id", ["missing", "A1"])
def test_get_history_unknown_id_raises_not_found(bank: Bank, account_id: str) -> None:
    """Asking for the history of an unknown id raises AccountNotFoundError."""
    with pytest.raises(AccountNotFoundError):
        bank.get_history(account_id)
