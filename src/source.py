from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from fractions import Fraction
import random
from importlib.metadata import distribution

from probs import Distribution, Sampler, switch_to_symbols
from source_format import Description, SourceDescription, MarkovDescription, MixtureDescription

type Source = PeriodicSource | MarkovSource | MixtureSource
type Component = tuple[Fraction, Source]

@dataclass(frozen=True)
class PeriodicSource:
    alphabet: tuple[str, ...]
    positions: tuple[Distribution, ...]
    samplers: tuple[Sampler, ...]

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

        samplers: tuple[Sampler] = tuple(Sampler.from_distribution(d) for d in positions)
        return cls(alphabet=alphabet, positions=tuple(positions), samplers=samplers)

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

    def generate(self, rng: random.Random) -> Iterator[str]:
        i = 0

        while True:
            sampler = self.samplers[i]
            i = (i + 1) % self.period
            yield sampler.sample(rng)


def period_average(source: PeriodicSource, block: Sequence[str]) -> Fraction:
    s = 0

    for i in range(1, source.period + 1):
        s += source.block_prob(block, i)

    return Fraction(s, source.period)


@dataclass(frozen=True)
class MarkovSource:
    depth: int
    alphabet: tuple[str, ...]
    initial: Distribution
    transitions: dict[str, Distribution]
    initial_sampler: Sampler
    samplers: dict[str, Sampler]

    @classmethod
    def from_description(cls, desc: MarkovDescription) -> "MarkovSource":
        initial_sampler = Sampler.from_distribution(desc.initial)
        samplers: dict[str, Sampler] = {
            context: Sampler.from_distribution(distribution)
            for context, distribution in desc.transitions.items()
        }

        return cls(
            depth=desc.depth,
            alphabet=desc.alphabet,
            initial=desc.initial,
            transitions=desc.transitions,
            initial_sampler=initial_sampler,
            samplers=samplers,
        )

    def context_dist_at(self, t: int) -> Distribution:
        if t < self.depth:
            raise ValueError("t must be greater than or equal to source's depth")

        if t == self.depth:
            return self.initial.copy()

        context_dist: Distribution = self.initial.copy()

        for _ in range(t - self.depth):
            new_context_dist: Distribution = {}
            for context in context_dist:
                transitions = self.transitions[context]

                for transition, prob in transitions.items():
                    new_context = _shift(context, transition)
                    new_context_dist[new_context] = new_context_dist.get(new_context, 0) + prob * context_dist[context]

            context_dist = new_context_dist

        return context_dist



    def block_prob(self, block: Sequence[str], start: int = 1) -> Fraction:
        if start < 1:
            raise ValueError("start must be greater than or equal to 1")

        prob = Fraction(0)
        block = tuple(block)

        if 1 <= start <= self.depth:
            distribution = self.initial
            offset = start - 1
            inside = min(len(block), self.depth - offset)
        else:
            distribution = self.context_dist_at(start - 1)
            offset = 0
            inside = 0

        for context, ctx_prob in distribution.items():
            splitted_ctx = tuple(context.split())

            if splitted_ctx[offset: offset + inside] != block[:inside]:
                continue

            for c in block[inside:]:
                ctx_prob *= self.transitions[context].get(c, 0)
                context = _shift(context, c)

            prob += ctx_prob

        return prob

    def generate(self, rng: random.Random) -> Iterator[str]:
        context = self.initial_sampler.sample(rng)

        for c in context.split():
            yield c

        while True:
            n = self.samplers[context].sample(rng)
            context = _shift(context, n)
            yield n

def _shift(context: str, symbol: str) -> str:
    symbols  = context.split()
    symbols.append(symbol)
    return " ".join(symbols[1:])

@dataclass(frozen=True)
class MixtureSource:
    components: tuple[Component, ...]
    alphabet: tuple[str, ...]
    sampler: Sampler

    @classmethod
    def from_description(cls, desc: MixtureDescription) -> "MixtureSource":
        components: list[Component] = []
        raw_alphabet: set[str] = set()

        for prob, component_desc in desc.components:
            source = source_from_description(component_desc)
            raw_alphabet.update(source.alphabet)
            components.append((prob, source))

        alphabet = tuple(sorted(raw_alphabet))
        distribution: Distribution = {
            str(i): component[0]
            for i, component in enumerate(components)
        }
        sampler = Sampler.from_distribution(distribution)

        return cls(
            components=tuple(components),
            alphabet=alphabet,
            sampler=sampler,
        )

    def block_prob(self, block: Sequence[str], start: int = 1) -> Fraction:
        prob = Fraction(0)

        for source_prob, source in self.components:
            if any(c not in source.alphabet for c in block):
                continue

            prob += source_prob * source.block_prob(block, start)

        return prob

    def generate(self, rng: random.Random) -> Iterator[str]:
        idx_s = self.sampler.sample(rng)
        idx = int(idx_s)
        _, source = self.components[idx]

        yield from source.generate(rng)

def source_from_description(desc: Description) -> Source:
    if isinstance(desc, SourceDescription):
        return PeriodicSource.from_description(desc)
    if isinstance(desc, MarkovDescription):
        return MarkovSource.from_description(desc)

    return MixtureSource.from_description(desc)
