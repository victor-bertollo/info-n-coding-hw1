# весь файл сгенерирован Claude (Anthropic), см. SOURCES.md
import argparse
import os
import random
import sys
from fractions import Fraction
from itertools import islice

from errors import InputError
from source import PeriodicSource, period_average
from source_format import load_description
from task11 import frequency_table
from variant import Variant


STUDENT_NUMBER = 3
TABLE_SIZES = (10**2, 10**3, 10**4, 10**5, 10**6)


def parse_length(text: str) -> int | None:
    if text == "None":
        return None
    try:
        return int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"expected integer or None, got {text!r}") from None


def positive_int(text: str) -> int:
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"expected positive integer, got {text!r}") from None
    if value <= 0:
        raise argparse.ArgumentTypeError(f"expected positive integer, got {value}")
    return value


def load_source(path: str) -> PeriodicSource:
    return PeriodicSource.from_description(load_description(path))


def single_char_alphabet(source: PeriodicSource) -> bool:
    return all(len(a) == 1 for a in source.alphabet)


def parse_block(source: PeriodicSource, words: list[str]) -> tuple[str, ...]:
    if single_char_alphabet(source):
        block = tuple("".join(words))
    else:
        block = tuple(words)
    if not block:
        raise InputError("block must contain at least one symbol")
    unknown = sorted(set(a for a in block if a not in source.alphabet))
    if unknown:
        raise InputError(f"symbols {unknown} are not in source alphabet {list(source.alphabet)}")
    return block


def fmt(p: Fraction) -> str:
    return f"{p} ≈ {float(p):.6f}"


def cmd_variant(args: argparse.Namespace) -> int:
    v = Variant.from_s(args.variant)
    print(f"variant: s = {v.s}")
    print(f"k = {v.k}, M = {v.M}, L = {v.L}, d = {v.d}, q = {v.q}, eps = {v.eps}")
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    source = load_source(args.source)
    stream = source.generate(random.Random(args.seed))
    if args.n is not None and args.n > 0:
        stream = islice(stream, args.n)
    sep = "" if single_char_alphabet(source) else " "
    out = sys.stdout
    first = True
    for symbol in stream:
        if not first:
            out.write(sep)
        out.write(symbol)
        first = False
    out.write("\n")
    return 0


def cmd_prob(args: argparse.Namespace) -> int:
    source = load_source(args.source)
    block = parse_block(source, args.block)
    r = len(block)
    if r > args.n:
        raise InputError(f"block length r = {r} exceeds N = {args.n}")

    table_sizes = [n for n in TABLE_SIZES if n >= r]
    sizes = sorted(set(table_sizes) | {args.n})
    rows = {row.n: row for row in frequency_table(source, block, random.Random(args.seed), sizes)}
    sep = "" if single_char_alphabet(source) else " "

    print(f"source: {args.source} (L = {source.period}, alphabet: {' '.join(source.alphabet)})")
    print(f"block: {sep.join(block)} (r = {r}), seed = {args.seed}")
    print(f"(1) Pr{{X_1..X_r = block}}: {fmt(source.block_prob(block, 1))}")
    print(f"(2) period average:       {fmt(period_average(source, block))}")
    print(f"(3) frequency, N = {args.n}: {fmt(rows[args.n].freq)}")
    print()
    if not table_sizes:
        print(f"table skipped: r = {r} exceeds every N in {list(TABLE_SIZES)}")
        return 0
    if len(table_sizes) < len(TABLE_SIZES):
        print(f"rows with N < r = {r} are skipped")
    print(f"{'N':>9}  {'frequency':>10}  {'|f - (1)|':>10}  {'|f - (2)|':>10}")
    for n in table_sizes:
        row = rows[n]
        print(f"{n:>9}  {float(row.freq):>10.6f}  {float(row.diff_first):>10.6f}  {float(row.diff_average):>10.6f}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="main.py", description="HW1: source coding")
    parser.add_argument(
        "--variant", nargs="?", const=STUDENT_NUMBER, type=int, metavar="S",
        help=f"print variant parameters (default S = {STUDENT_NUMBER}) and exit",
    )
    tasks = parser.add_subparsers(dest="task")

    seed = argparse.ArgumentParser(add_help=False)
    seed.add_argument("--seed", type=int, default=0, help="random seed (default 0)")

    t11 = tasks.add_parser("task11", help="task 1.1: discrete source modelling")
    modes = t11.add_subparsers(dest="mode", required=True)

    gen = modes.add_parser(
        "generate", parents=[seed],
        help="mode 1: realization of length N; N = None or N <= 0 runs until Ctrl+C",
    )
    gen.add_argument("source", help="source description (json)")
    gen.add_argument("n", type=parse_length, metavar="N", help="length or None")
    gen.set_defaults(handler=cmd_generate)

    prob = modes.add_parser(
        "prob", parents=[seed],
        help="mode 2: exact block probabilities and frequency estimate",
    )
    prob.add_argument("source", help="source description (json)")
    prob.add_argument("n", type=positive_int, metavar="N", help="realization length, N > 0")
    prob.add_argument("block", nargs="+", metavar="SYMBOL", help="block a_1 ... a_r")
    prob.set_defaults(handler=cmd_prob)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.variant is not None:
        return cmd_variant(args)
    if args.task is None:
        parser.print_help(sys.stderr)
        return 2
    try:
        return args.handler(args)
    except InputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        sys.stdout.write("\n")
        return 130
    except BrokenPipeError:
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        return 0


if __name__ == "__main__":
    sys.exit(main())
