from collections import deque
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from fractions import Fraction
import random

from source import PeriodicSource, period_average


@dataclass(frozen=True)
class Frequency:
    n: int
    freq: Fraction
    diff_first: Fraction
    diff_average: Fraction


def count_matches(
    stream: Iterable[str], block: Sequence[str], sizes: Sequence[int]
) -> dict[int, int]:
    matches: dict[int, int] = {}
    block = tuple(block)
    block_len = len(block)
    window = deque(maxlen=block_len)
    stop = max(sizes)
    counter = 0

    for t, symbol in enumerate(stream, start=1):
        window.append(symbol)

        if t >= block_len and tuple(window) == block:
            counter += 1

        if t in sizes:
            matches[t] = counter

        if t == stop:
            break

    return matches


def frequency_table(
    source: PeriodicSource, block: Sequence[str], rng: random.Random, sizes: Sequence[int]
) -> list[Frequency]:
    p_first = source.block_prob(block, 1)
    p_avg = period_average(source, block)
    matches = count_matches(source.generate(rng), block, sizes)
    block_len = len(block)
    frequencies: list[Frequency] = []

    for n in sizes:
        freq = Fraction(matches[n], n - block_len + 1)
        diff_first = abs(freq - p_first)
        diff_average = abs(freq - p_avg)
        frequencies.append(
            Frequency(n=n, freq=freq, diff_first=diff_first, diff_average=diff_average)
        )

    return frequencies
