"""Tests for the Bank class in bank.py. All money values are int cents."""

import pytest

from account import Account
from bank import Bank
from errors import (
    AccountNotFoundError,
    BankError,
    DuplicateAccountError,
    InsufficientFundsError,
    InvalidAccountIdError,
    InvalidAmountError,
)


@pytest.fixture
def bank() -> Bank:
    """Return a bank with two accounts: a1 has 1000 cents, a2 has 0."""
    return Bank([Account("a1", 1000), Account("a2")])


def test_bank_starts_with_existing_accounts(bank: Bank) -> None:
    """Accounts given to the constructor can be found with their balances."""
    assert bank.get_account("a1").get_balance() == 1000
    assert bank.get_account("a2").get_balance() == 0


def test_duplicate_ids_in_starting_accounts_raise() -> None:
    """Two starting accounts with the same id are rejected."""
    with pytest.raises(DuplicateAccountError):
        Bank([Account("x", 100), Account("x", 200)])


def test_open_account_then_find_it(bank: Bank) -> None:
    """A newly opened account is returned and can be found by its id."""
    account = bank.open_account("a3", 500)
    assert bank.get_account("a3") is account
    assert account.get_balance() == 500


def test_open_duplicate_id_raises_and_keeps_original(bank: Bank) -> None:
    """Opening an id that already exists fails and keeps the old account."""
    original = bank.get_account("a1")
    with pytest.raises(DuplicateAccountError):
        bank.open_account("a1", 99)
    assert bank.get_account("a1") is original
    assert original.get_balance() == 1000


def test_deposit_and_withdraw_by_id_update_balance(bank: Bank) -> None:
    """Deposit and withdraw by id return and store the new balance."""
    assert bank.deposit("a1", 250) == 1250
    assert bank.withdraw("a1", 1250) == 0
    assert bank.get_account("a1").get_balance() == 0


def test_actions_on_one_account_do_not_affect_others(bank: Bank) -> None:
    """Changing one account leaves every other account unchanged."""
    bank.deposit("a2", 300)
    bank.withdraw("a1", 400)
    assert bank.get_account("a1").get_balance() == 600
    assert bank.get_account("a2").get_balance() == 300


@pytest.mark.parametrize(
    "call",
    [
        lambda b: b.get_account("missing"),
        lambda b: b.deposit("missing", 100),
        lambda b: b.withdraw("missing", 100),
        # Matching is exact, so case and spaces matter.
        lambda b: b.get_account("A1"),
        lambda b: b.get_account(" a1"),
    ],
    ids=["find", "deposit", "withdraw", "wrong-case", "extra-space"],
)
def test_unknown_id_raises_not_found(bank: Bank, call) -> None:
    """Unknown ids raise AccountNotFoundError, which is a BankError and a LookupError."""
    with pytest.raises(AccountNotFoundError) as exc_info:
        call(bank)
    assert isinstance(exc_info.value, BankError)
    assert isinstance(exc_info.value, LookupError)


@pytest.mark.parametrize(
    ("action", "amount", "error"),
    [
        ("deposit", 0, InvalidAmountError),
        ("withdraw", -5, InvalidAmountError),
        ("deposit", 10.5, TypeError),
        ("withdraw", 1001, InsufficientFundsError),
    ],
)
def test_invalid_amount_or_overdraw_raises_and_keeps_balance(
    bank: Bank, action: str, amount: object, error: type[Exception]
) -> None:
    """Bad amounts and overdraws raise through the bank and change nothing."""
    with pytest.raises(error):
        getattr(bank, action)("a1", amount)
    assert bank.get_account("a1").get_balance() == 1000


@pytest.mark.parametrize(
    ("account_id", "balance", "error"),
    [
        ("", 0, InvalidAccountIdError),
        ("   ", 0, InvalidAccountIdError),
        ("a3", -1, InvalidAmountError),
        ("a3", 10.5, TypeError),
    ],
)
def test_failed_open_does_not_add_account(
    bank: Bank, account_id: str, balance: object, error: type[Exception]
) -> None:
    """A rejected open_account call leaves no account behind for that id."""
    with pytest.raises(error):
        bank.open_account(account_id, balance)  # type: ignore[arg-type]
    with pytest.raises(AccountNotFoundError):
        bank.get_account(account_id)


@pytest.mark.parametrize(
    "call",
    [
        lambda b: b.get_account(123),
        lambda b: b.deposit(None, 100),
        lambda b: b.withdraw(1, 100),
        lambda b: b.open_account(123),
    ],
    ids=["find", "deposit", "withdraw", "open"],
)
def test_non_string_id_raises_type_error(bank: Bank, call) -> None:
    """Every Bank method rejects an account id that is not a str."""
    with pytest.raises(TypeError):
        call(bank)
