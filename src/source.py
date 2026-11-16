from collections import deque
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from fractions import Fraction
import random

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

    def context_kernel(self) -> dict[str, Distribution]:
        distributions: dict[str, Distribution] = {}

        for context, ctx_d in self.transitions.items():
            distribution: Distribution = {}

            for n, prob in ctx_d.items():
                new_ctx = _shift(context, n)
                distribution[new_ctx] = prob

            distributions[context] = distribution

        return distributions

def _reachable(kernel: dict[str, Distribution], start: str) -> set[str]:
    reachable: set[str] = set()
    d = deque([start])

    while d:
        n = d.popleft()

        if n in reachable:
            continue

        reachable.add(n)

        if n not in kernel:
            continue

        distribution = kernel[n]

        for c, prob in distribution.items():
            if prob > 0:
                d.append(c)

    return reachable

def _closed_classes(kernel: dict[str, Distribution]) -> list[set[str]]:
    reachable: dict[str, set[str]] = {context: _reachable(kernel, context) for context in kernel}
    result: list[set[str]] = []

    for context, group in reachable.items():
        if all(context in reachable[reachable_ctx] for reachable_ctx in group) and group not in result:
            result.append(group)

    return result

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

# Begin OpenAI Codex generated code: exact long-run block average.

def _solve_linear(
    a: list[list[Fraction]],
    b: list[Fraction],
) -> list[Fraction]:
    """Solve a square linear system using exact Gaussian elimination."""
    n = len(b)

    if len(a) != n or any(len(row) != n for row in a):
        raise ValueError("expected a square matrix matching b")

    rows = [
        [Fraction(x) for x in row] + [Fraction(y)]
        for row, y in zip(a, b)
    ]

    for col in range(n):
        pivot = next(
            (i for i in range(col, n) if rows[i][col] != 0),
            None,
        )
        if pivot is None:
            raise ValueError("linear system has no unique solution")

        rows[col], rows[pivot] = rows[pivot], rows[col]

        divisor = rows[col][col]
        rows[col] = [x / divisor for x in rows[col]]

        for i in range(n):
            if i == col:
                continue

            factor = rows[i][col]
            if factor:
                rows[i] = [
                    x - factor * y
                    for x, y in zip(rows[i], rows[col])
                ]

    return [row[-1] for row in rows]


def _stationary_distribution(
    kernel: dict[str, Distribution],
    group: set[str],
) -> Distribution:
    """Find the invariant distribution inside one closed class."""
    states = sorted(group)
    n = len(states)

    # Balance equations: incoming probability equals current probability.
    a = [
        [
            kernel[src].get(dst, Fraction(0)) - Fraction(i == j)
            for j, src in enumerate(states)
        ]
        for i, dst in enumerate(states)
    ]
    b = [Fraction(0)] * n

    # Replace one redundant equation with sum(probabilities) = 1.
    a[-1] = [Fraction(1)] * n
    b[-1] = Fraction(1)

    return dict(zip(states, _solve_linear(a, b)))


def _average_context_distribution(
    source: MarkovSource,
) -> Distribution:
    """Find the limiting average distribution of contexts."""
    kernel = source.context_kernel()
    groups = _closed_classes(kernel)

    recurrent = set().union(*groups)
    transient = sorted(set(kernel) - recurrent)

    # Absorption equations for transient states: (I - Q) h = b.
    a = [
        [
            Fraction(i == j) - kernel[x].get(y, Fraction(0))
            for j, y in enumerate(transient)
        ]
        for i, x in enumerate(transient)
    ]

    result: Distribution = {}

    for group in groups:
        b = [
            sum(
                (kernel[x].get(y, Fraction(0)) for y in group),
                Fraction(0),
            )
            for x in transient
        ]
        absorption = _solve_linear(a, b)

        # Include both initial mass in the class and eventual arrivals.
        weight = sum(
            (source.initial.get(x, Fraction(0)) for x in group),
            Fraction(0),
        )
        weight += sum(
            (
                source.initial.get(x, Fraction(0)) * h
                for x, h in zip(transient, absorption)
            ),
            Fraction(0),
        )

        if weight == 0:
            continue

        stationary = _stationary_distribution(kernel, group)

        for context, prob in stationary.items():
            result[context] = weight * prob

    return result


def average_block_prob(
    source: Source,
    block: Sequence[str],
) -> Fraction:
    """Return the limit of block probabilities averaged over positions."""
    block = tuple(block)

    if any(symbol not in source.alphabet for symbol in block):
        return Fraction(0)

    if isinstance(source, PeriodicSource):
        return period_average(source, block)

    if isinstance(source, MixtureSource):
        return sum(
            (
                weight * average_block_prob(component, block)
                for weight, component in source.components
                if weight > 0
            ),
            Fraction(0),
        )

    result = Fraction(0)

    for context, prob in _average_context_distribution(source).items():
        # Emit the block after a context with the invariant distribution.
        for symbol in block:
            prob *= source.transitions[context].get(symbol, Fraction(0))

            if prob == 0:
                break

            context = _shift(context, symbol)

        result += prob

    return result

# End OpenAI Codex generated code.