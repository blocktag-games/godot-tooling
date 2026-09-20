#!/usr/bin/env python3
"""BP10: the frozen main-study scheduling algorithm, per docs/
benchmarks/performance-protocol.md's item 4 ("Frozen concrete
algorithm 2026-09-20") -- NOT the BP07 pilot's simpler per-block
`random.Random(seed).shuffle()`, which was explicitly scoped to the
pilot only (see pilot/performance/run_pilot.py's own module comment)
and does not implement real AB/BA/permutation balance.

Two balancing schemes, both giving EXACT per-position condition
balance by construction (not merely balanced in expectation):

- Three-condition candidates (gd-tools: B0/B1/C): the 6 permutations of
  (B0, B1, C), shuffled in order and assigned one per block. Verified
  directly (not assumed): the six permutations' first elements are
  {B0, B0, B1, B1, C, C}, second {B1, C, B0, C, B0, B1}, third {C, B1,
  C, B0, B1, B0} -- each condition appears in each ordinal position
  exactly twice, regardless of shuffle order.
- Two-condition candidates (Nano Coverage: B0/C): the list
  [AB, AB, AB, BA, BA, BA] (three of each), shuffled in order.

Both require the session's own block count to be an exact multiple of
the scheme's natural cycle length (6 for three-condition, 2 for
two-condition) -- this module refuses to guess a fallback for any other
block count, per the protocol's explicit instruction not to silently
truncate or repeat without documenting the choice.

Seed scoping (disambiguated after a BP09 review found the first
version of the protocol text left this ambiguous): each (candidate,
workload) cell gets its OWN within-session block-order seed, distinct
from the one cross-cell seed shared by all cells in that session.
"""
from __future__ import annotations

import hashlib
import random
from itertools import permutations

THREE_CONDITION_PERMUTATIONS = list(permutations(["B0", "B1", "C"]))  # 6 permutations
assert len(THREE_CONDITION_PERMUTATIONS) == 6


def block_order_seed(candidate_name: str, workload: str, session: int) -> int:
    key = f"{candidate_name}:{workload}:{session}:block-order".encode()
    return int.from_bytes(hashlib.sha256(key).digest()[:4], "big")


def cross_cell_seed(session: int) -> int:
    key = f"{session}:cross-cell".encode()
    return int.from_bytes(hashlib.sha256(key).digest()[:4], "big")


def three_condition_block_orders(seed: int, n_blocks: int) -> list[tuple[str, str, str]]:
    if n_blocks != 6:
        raise ValueError(
            f"three_condition_block_orders: n_blocks={n_blocks} is not a multiple of 6 "
            f"(the permutation cycle length) -- the frozen algorithm has no fallback for "
            f"this; choose and document a repeat/truncate rule before changing n_blocks "
            f"from its frozen default of 6."
        )
    orders = THREE_CONDITION_PERMUTATIONS[:]
    random.Random(seed).shuffle(orders)
    return orders


def two_condition_block_orders(seed: int, n_blocks: int) -> list[tuple[str, str]]:
    if n_blocks % 2 != 0:
        raise ValueError(
            f"two_condition_block_orders: n_blocks={n_blocks} is odd -- AB/BA cannot be "
            f"exactly balanced; choose and document a rule before changing n_blocks from "
            f"its frozen default of 6."
        )
    half = n_blocks // 2
    orders: list[tuple[str, str]] = [("B0", "C")] * half + [("C", "B0")] * half
    random.Random(seed).shuffle(orders)
    return orders


def cross_cell_order(seed: int, cells: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Shuffles the execution order of (candidate, workload) cells
    within a session, using the session's own cross-cell seed --
    independent of any cell's internal block-order seed above."""
    order = cells[:]
    random.Random(seed).shuffle(order)
    return order
