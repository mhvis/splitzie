from collections import namedtuple
from decimal import Decimal
from itertools import permutations
from typing import Hashable, NamedTuple, Any, Generator, Iterable, Iterator


class SettleEntry(NamedTuple):
    id: Any
    balance: Decimal


class Move(NamedTuple):
    source: Any
    target: Any
    amount: Decimal


class Settler:
    """Settle a list of balances.

    Sources:

    - https://en.wikipedia.org/wiki/Bin_packing_problem
    - https://stackoverflow.com/q/1163116/2373688
    - https://stackoverflow.com/q/877728/2373688
    """

    creditors: list[SettleEntry]
    debtors: list[SettleEntry]

    def __init__(self, entries: list[SettleEntry]):
        """Sets the balances for this instance.

        Args:
            entries: A list of two-tuples with an identifier (e.g. integer)
                and the balance.
        """
        if sum(e.balance for e in entries) != 0:
            raise ValueError("Balances must sum to 0")
        self.creditors = [e for e in entries if e.balance > 0]
        self.debtors = [e for e in entries if e.balance < 0]

    @staticmethod
    def get_moves(creditors, debtors) -> list[Move]:
        """Runs the algorithm and returns the moves.

        The order of entries determines how optimal the solution is. Different
        orderings may give more optimal solutions.
        """
        if len(debtors) == 0:
            # In this case, creditors will also be empty.
            return []

        # Current index and remaining balance
        c = 0
        c_remaining = creditors[c].balance

        moves = []
        for d in range(len(debtors)):
            # Remaining balance for the current debtor (amount is negative)
            d_remaining = debtors[d].balance

            while d_remaining < 0:
                if c_remaining == 0:
                    # Current creditor is exhausted. Move on to the next.
                    #
                    # (There will always be a next creditor.)
                    c += 1
                    c_remaining = creditors[c].balance

                amount = min(-d_remaining, c_remaining)

                moves.append(Move(debtors[d].id, creditors[c].id, amount))

                d_remaining += amount
                c_remaining -= amount

        return moves

    def get_optimal_brute_force(self, limit=7) -> list[Move]:
        """Will take ages when group is moderately large.

        Args:
            limit: When the number of creditors or debtors is larger than the
                limit, we don't find the optimal but just return *a* solution.
        """
        if len(self.creditors) + len(self.debtors) > limit:
            return Settler.get_moves(self.creditors, self.debtors)

        optimal = None

        for credit_perm in permutations(self.creditors):
            for debtor_perm in permutations(self.debtors):
                moves = Settler.get_moves(credit_perm, debtor_perm)
                if optimal is None or len(moves) < len(optimal):
                    optimal = moves

        return optimal
