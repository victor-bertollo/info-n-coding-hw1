from fractions import Fraction

from errors import InputError


type Distribution = dict[str, Fraction]


def parse_prob(text: object | str, where: str) -> Fraction:
    if not isinstance(text, str):
        raise InputError(f"{where} must be str object")

    text = text.strip()

    if not text:
        raise InputError(f"{where} must be non-empty string")

    try:
        f = Fraction(text)
    except (ValueError, ZeroDivisionError) as exc:
        raise InputError(f"failed to parse {where} as fraction") from exc

    if f < 0:
        raise InputError(f"{where} can't be less than 0")

    return f


def parse_distribution(obj: object | dict, where: str) -> Distribution:
    if not isinstance(obj, dict) or not obj:
        raise InputError(f"{where} must be non-empty dict")

    distribution: Distribution = {}
    distribution_sum = 0

    for k, v in obj.items():
        if not isinstance(k, str):
            raise InputError(f"{where} keys must be string")

        prob_where = f"{where}[{k!r}]"
        prob = parse_prob(v, prob_where)
        distribution_sum += prob
        distribution[k] = prob

    if distribution_sum != 1:
        raise InputError(f"sum of {where} should be equal to 1, got {distribution_sum}")

    return distribution


def switch_to_symbols(
    weights: Distribution, components: dict[str, Distribution], alphabet: tuple[str, ...]
) -> Distribution:
    result: Distribution = {}

    for c in alphabet:
        result[c] = sum(weights[m] * components[m].get(c, 0) for m in weights)

    return result
