"""Records of money movements, used for an account's transaction history."""

from dataclasses import dataclass
from enum import Enum


class TransactionKind(Enum):
    """The type of money movement a transaction records."""

    OPENING = "opening"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"


# frozen=True: money history must never be edited after it is written.
@dataclass(frozen=True)
class Transaction:
    """One successful money movement on one account.

    Attributes:
        kind: The type of movement.
        amount: The cents moved. Always > 0.
        balance_after: The account balance in cents right after this movement.
        related_account_id: The other account's id for a transfer, else None.
    """

    kind: TransactionKind
    amount: int
    balance_after: int
    related_account_id: str | None = None
