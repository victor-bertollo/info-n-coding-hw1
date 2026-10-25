from dataclasses import dataclass
from fractions import Fraction
import itertools
import json

from errors import InputError
from probs import Distribution, parse_distribution, parse_prob

type Description = SourceDescription | MarkovDescription | MixtureDescription
DESCRIPTION_TYPES = ["periodic", "markov", "mixture"]
PERIODIC_KEYS = ["models", "switches", "source"]
MARKOV_KEYS = ["depth", "alphabet", "initial", "transitions"]
MIXTURE_KEYS = ["components"]
COMPONENT_KEYS = ["weight", "source"]


@dataclass(frozen=True)
class SourceDescription:
    models: dict[str, Distribution]
    switches: dict[str, Distribution]
    source: tuple[str, ...]


@dataclass(frozen=True)
class MarkovDescription:
    depth: int
    alphabet: tuple[str, ...]
    initial: Distribution
    transitions: dict[str, Distribution]


@dataclass(frozen=True)
class MixtureDescription:
    components: tuple[tuple[Fraction, Description], ...]


def load_description(path: str) -> Description:
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)

        return parse_description(data)
    except OSError as exc:
        raise InputError(f"failed to open file {path}: {exc.strerror}") from exc
    except UnicodeDecodeError as exc:
        raise InputError(f"file {path} not in UTF-8") from exc
    except json.JSONDecodeError as exc:
        raise InputError(f"file {path} content is not a valid json") from exc
    except RecursionError as exc:
        raise InputError(f"source {path} contains recursion error") from exc


def _check_data_keys(data: dict[str, object], keys: list[str]):
    for k in keys:
        if k not in data:
            raise InputError(f"data must have key {k}")


def parse_description(data: object | dict[str, object]) -> Description:
    if not isinstance(data, dict):
        raise InputError("data is not a dict")

    match data.get("type", "periodic"):
        case "periodic":
            return _parse_periodic(data)
        case "markov":
            return _parse_markov(data)
        case "mixture":
            return _parse_mixture(data)
        case _:
            raise InputError("incorrect description type")


def _parse_periodic(data: dict[str, object]) -> SourceDescription:
    _check_data_keys(data, PERIODIC_KEYS)
    models = _parse_models(data["models"])
    switches = _parse_switches(data["switches"], models)
    source = _parse_source(data["source"], switches)
    return SourceDescription(models=models, switches=switches, source=source)


def _parse_models(obj: object | dict[str, object]) -> dict[str, Distribution]:
    if not isinstance(obj, dict) or not obj:
        raise InputError('"models" must be non-empty dict')

    models = {}

    for k, v in obj.items():
        where = f"models[{k!r}]"
        models[k] = parse_distribution(v, where)

    return models


def _parse_switches(obj: object | dict, models: dict[str, Distribution]) -> dict[str, Distribution]:
    if not isinstance(obj, dict) or not obj:
        raise InputError('"switches" must be non-empty dict')

    switches = {}

    for k, v in obj.items():
        if not isinstance(k, str):
            raise InputError('"switches" keys must be string')

        where = f"switches[{k!r}]"
        distribution = parse_distribution(v, where)

        for model in distribution:
            if model not in models:
                raise InputError(f"{model} model doesn't exist")

        switches[k] = distribution

    return switches


def _parse_source(obj: object | list, switches: dict[str, Distribution]) -> tuple[str, ...]:
    if not isinstance(obj, list) or not obj:
        raise InputError('"source" must be non-empty list')

    source = tuple(obj)

    for switch in source:
        if not isinstance(switch, str):
            raise InputError('"source" values must be string')

        if switch not in switches:
            raise InputError(f"{switch} switch doesn't exist")

    return source


def _parse_markov(data: dict[str, object]) -> MarkovDescription:
    _check_data_keys(data, MARKOV_KEYS)
    depth = _parse_depth(data["depth"])
    alphabet = _parse_alphabet(data["alphabet"])
    contexts = set(_all_contexts(alphabet, depth))
    initial = _parse_initial(data["initial"], contexts)
    transitions = _parse_transitions(data["transitions"], contexts, alphabet)
    return MarkovDescription(depth=depth, alphabet=alphabet, initial=initial, transitions=transitions)


def _parse_depth(obj: object | int) -> int:
    if type(obj) != int or obj <= 0:
        raise InputError('"depth" must be an integer greater than 0')

    return obj


def _parse_alphabet(obj: object | list) -> tuple[str, ...]:
    if not isinstance(obj, list) or not obj:
        raise InputError('"alphabet" must be non-empty list of strings')

    seen: set[str] = set()

    for v in obj:
        if not isinstance(v, str) or not v or " " in v or v in seen:
            raise InputError('"alphabet" symbol must be unique non-empty string without spaces')

        seen.add(v)

    return tuple(obj)


def _all_contexts(alphabet: tuple[str, ...], depth: int) -> list[str]:
    result = itertools.product(alphabet, repeat=depth)
    return [" ".join(c) for c in result]


def _parse_initial(obj: object | dict[str, object], contexts: set[str]) -> Distribution:
    distribution = parse_distribution(obj, "initial")

    for k in distribution:
        if k not in contexts:
            raise InputError(f"{k} context doesn't exist")

    return distribution

def _parse_transitions(obj: object | dict[str, object], contexts: set[str], alphabet: tuple[str]) -> dict[str, Distribution]:
    if not isinstance(obj, dict) or not obj:
        raise InputError('"transitions" must be non-empty dict')

    not_seen = contexts.copy()
    transitions: dict[str, Distribution] = {}
    keys = set(obj.keys())

    for c in contexts:
        if c not in obj:
            raise InputError(f"{c} context doesn't exist")

        where = f"transitions[{c!r}]"
        distribution = parse_distribution(obj[c], where)

        for s in distribution:
            if s not in alphabet:
                raise InputError(f"alphabet doesn't have {s} symbol")

        transitions[c] = distribution
        not_seen.remove(c)
        keys.remove(c)

    keys_left = keys - not_seen

    if keys_left:
        exc_msg = "unknown contexts in transitions: " + ", ".join(sorted(keys_left))
        raise InputError(exc_msg)

    if not not_seen:
        return transitions

    exc_msg = "missed contexts in transitions: " + ", ".join(sorted(not_seen))
    raise InputError(exc_msg)

def _parse_mixture(data: dict[str, object]) -> MixtureDescription:
    _check_data_keys(data, MIXTURE_KEYS)
    components = _parse_components(data["components"])
    return MixtureDescription(components)


def _parse_components(obj: object | list) -> tuple[tuple[Fraction, Description], ...]:
    if not isinstance(obj, list) or not obj:
        raise InputError('"components" must be non-empty list')

    components: list[tuple[Fraction, Description]] = []
    components_sum = Fraction(0)

    for i, c in enumerate(obj):
        where = f"components[{i}]"
        weight, source = _parse_component(c, where)
        components_sum += weight
        components.append((weight, source))

    if components_sum != Fraction(1):
        raise InputError(f"sum of components' weights should be equal to 1, got {components_sum}")

    return tuple(components)

def _parse_component(obj: object | dict[str, object], where: str) -> tuple[Fraction, Description]:
    if not isinstance(obj, dict) or not obj:
        raise InputError('"components" must be non-empty dict')

    _check_data_keys(obj, COMPONENT_KEYS)
    prob_where = where + '["weight]'
    weight = parse_prob(obj["weight"], where=prob_where)
    source = parse_description(obj["source"])
    return weight, source