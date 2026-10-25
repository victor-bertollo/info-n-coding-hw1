from dataclasses import dataclass
import json

from errors import InputError
from probs import Distribution, parse_distribution


DATA_KEYS = ["models", "switches", "source"]


@dataclass(frozen=True)
class SourceDescription:
    models: dict[str, Distribution]
    switches: dict[str, Distribution]
    source: tuple[str, ...]


def load_description(path: str) -> SourceDescription:
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except OSError as exc:
        raise InputError(f"failed to open file {path}: {exc.strerror}") from exc
    except UnicodeDecodeError as exc:
        raise InputError(f"file {path} not in UTF-8") from exc
    except json.JSONDecodeError as exc:
        raise InputError(f"file {path} content is not a valid json") from exc

    return parse_description(data)


def parse_description(data: object | dict[str, object]) -> SourceDescription:
    if not isinstance(data, dict):
        raise InputError("data is not a dict")

    for k in DATA_KEYS:
        if k not in data:
            raise InputError(f"data has no key {k}")

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
