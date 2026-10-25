from collections.abc import Sequence
from dataclasses import dataclass
from fractions import Fraction

from probs import Distribution, switch_to_symbols
from source_format import SourceDescription


@dataclass(frozen=True)
class PeriodicSource:
    alphabet: tuple[str, ...]
    positions: tuple[Distribution, ...]

    @classmethod
    def from_description(cls, desc: SourceDescription) -> "PeriodicSource":
        raw_alphabet: set[str] = set()

        for model in desc.models.values():
            raw_alphabet |= model.keys()

        alphabet = tuple(sorted(raw_alphabet))
        positions: list[Distribution] = []

        for switch in desc.source:
            weights = desc.switches[switch]
            components = desc.models
            positions.append(switch_to_symbols(weights, components, alphabet))

        return cls(alphabet=alphabet, positions=tuple(positions))

    @property
    def period(self) -> int:
        return len(self.positions)

    def dist_at(self, i: int) -> Distribution:
        if i < 1:
            raise ValueError("i must be greater than 0")

        return self.positions[(i - 1) % self.period].copy()

    def block_prob(self, block: Sequence[str], start: int = 1) -> Fraction:
        prob = Fraction(1)

        for i, s in enumerate(block):
            prob *= self.dist_at(start + i)[s]

        return prob


def period_average(source: PeriodicSource, block: Sequence[str]) -> Fraction:
    s = 0

    for i in range(1, source.period + 1):
        s += source.block_prob(block, i)

    return s / source.period
