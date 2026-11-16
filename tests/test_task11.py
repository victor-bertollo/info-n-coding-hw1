# Begin OpenAI Codex generated code: task 1.1 regression tests.
import itertools
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from fractions import Fraction as F

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from source import source_from_description, average_block_prob, _solve_linear
from source_format import load_description, parse_description
from task11 import count_matches, frequency_table

DATA = ROOT / 'tests' / 'task11'


def source(name):
    return source_from_description(load_description(str(DATA / name)))


class MathematicsTests(unittest.TestCase):
    def test_periodic_reference(self):
        s = source('example2.json')
        self.assertEqual(s.block_prob('00'), F(17, 60))
        self.assertEqual(average_block_prob(s, '00'), F(527, 1800))

    def test_markov_cycle(self):
        s = source('markov.json')
        self.assertEqual(''.join(itertools.islice(s.generate(random.Random(3)), 12)), 'abcdeabcdeab')
        self.assertEqual(s.block_prob('ab'), 1)
        self.assertEqual(s.block_prob('ab', 2), 0)
        self.assertEqual(average_block_prob(s, 'ab'), F(1, 5))
        row = frequency_table(s, F(1), F(1, 5), 'ab', random.Random(3), [1000])[0]
        self.assertEqual(row.freq, F(200, 999))

    def test_stationary_cycle(self):
        s = source('markov_stationary.json')
        for start in range(1, 12):
            self.assertEqual(s.block_prob('ab', start), F(1, 5))
        self.assertEqual(average_block_prob(s, 'ab'), F(1, 5))

    def test_absorption_and_initial_distribution(self):
        s = source('markov_absorption.json')
        self.assertEqual(s.block_prob('a'), 1)
        self.assertEqual(average_block_prob(s, 'a'), 0)
        self.assertEqual(average_block_prob(s, 'bc'), F(1, 6))
        self.assertEqual(average_block_prob(s, 'de'), F(1, 3))
        data = json.loads((DATA / 'markov_absorption.json').read_text())
        data['initial'] = {'a': '1/2', 'b': '1/2'}
        s = source_from_description(parse_description(data))
        self.assertEqual(average_block_prob(s, 'bc'), F(1, 3))
        self.assertEqual(average_block_prob(s, 'de'), F(1, 6))

    def test_mixture_probabilities(self):
        s = source('mixture.json')
        self.assertEqual(s.block_prob('a'), F(3, 8))
        self.assertEqual(average_block_prob(s, 'a'), F(3, 8))
        self.assertEqual(s.block_prob('aa'), F(5, 32))
        self.assertNotEqual(s.block_prob('aa'), F(3, 8) ** 2)
        self.assertEqual(average_block_prob(source('mixture_nested.json'), 'a'), F(31, 120))
        self.assertEqual(average_block_prob(source('degenerate/mixture_zero_weight.json'), 'a'), F(1, 4))

    def test_component_is_chosen_once(self):
        def constant(symbol):
            return {'models': {'m': {symbol: '1'}}, 'switches': {'s': {'m': '1'}}, 'source': ['s']}
        data = {'type': 'mixture', 'components': [
            {'weight': '1/2', 'source': constant('a')},
            {'weight': '1/2', 'source': constant('b')},
        ]}
        s = source_from_description(parse_description(data))
        self.assertEqual(s.block_prob('ab'), 0)
        self.assertEqual(average_block_prob(s, 'ab'), 0)
        for seed in range(20):
            self.assertEqual(len(set(itertools.islice(s.generate(random.Random(seed)), 100))), 1)

    def test_depth_two_boundary(self):
        s = source('degenerate/markov_depth2.json')
        self.assertEqual(s.block_prob('ababa'), 1)
        self.assertEqual(s.block_prob('baba', 2), 1)
        self.assertEqual(s.block_prob('aaba'), 0)
        self.assertEqual(average_block_prob(s, 'ab'), F(1, 2))

    def test_exact_enumeration(self):
        # Independent full-path enumeration checks all positions across initial contexts.
        for depth in (1, 2, 3):
            contexts = [' '.join(c) for c in itertools.product('ab', repeat=depth)]
            data = {'type': 'markov', 'depth': depth, 'alphabet': ['a', 'b'],
                    'initial': {c: str(F(i + 1, sum(range(1, len(contexts) + 1)))) for i, c in enumerate(contexts)},
                    'transitions': {c: {'a': str(F(i % 3 + 1, 4)), 'b': str(1 - F(i % 3 + 1, 4))} for i, c in enumerate(contexts)}}
            s = source_from_description(parse_description(data))
            paths = {tuple(c.split()): p for c, p in s.initial.items()}
            for _ in range(4):
                paths = {path + (symbol,): p * s.transitions[' '.join(path[-depth:])][symbol]
                         for path, p in paths.items() for symbol in 'ab'}
            for start in range(1, depth + 3):
                for length in (1, 2, 3):
                    for block in itertools.product('ab', repeat=length):
                        expected = sum(p for path, p in paths.items() if path[start-1:start-1+length] == block)
                        self.assertEqual(s.block_prob(block, start), expected)
            for length in (1, 2, 3):
                self.assertEqual(sum(average_block_prob(s, b) for b in itertools.product('ab', repeat=length)), 1)

    def test_overlapping_windows(self):
        self.assertEqual(count_matches('aaaa', 'aa', [2, 3, 4]), {2: 1, 3: 2, 4: 3})
        self.assertEqual(count_matches('abcde', 'aa', [2, 5]), {2: 0, 5: 0})

    def test_solver(self):
        self.assertEqual(_solve_linear([[0, 1], [2, 1]], [1, 5]), [F(2), F(1)])
        self.assertEqual(_solve_linear([], []), [])
        with self.assertRaises(ValueError):
            _solve_linear([[1, 1], [2, 2]], [1, 2])


class CliTests(unittest.TestCase):
    def cli(self, *args):
        return subprocess.run([sys.executable, str(ROOT / 'src/main.py'), *map(str, args)],
                              capture_output=True, text=True, timeout=30)

    def test_reproducibility_and_length(self):
        for name in ('variant.json', 'markov.json', 'mixture.json', 'mixture_nested.json'):
            with self.subTest(name=name):
                a = self.cli('task11', 'generate', DATA / name, 100, '--seed', 3)
                b = self.cli('task11', 'generate', DATA / name, 100, '--seed', 3)
                self.assertEqual(a.returncode, 0, a.stderr)
                self.assertEqual(a.stdout, b.stdout)
                self.assertEqual(len(a.stdout.strip()), 100)

    def test_prob_all_source_types(self):
        for name, block, first, avg in (
            ('example2.json', '00', '17/60', '527/1800'),
            ('markov.json', 'ab', '1 ≈', '1/5'),
            ('mixture.json', 'a', '3/8', '3/8'),
            ('markov_absorption.json', 'bc', '0 ≈', '1/6'),
            ('degenerate/markov_single.json', 'xx', '1 ≈', '1 ≈'),
        ):
            with self.subTest(name=name):
                p = self.cli('task11', 'prob', DATA / name, 1000, block, '--seed', 3)
                self.assertEqual(p.returncode, 0, p.stderr)
                self.assertIn(first, p.stdout.splitlines()[2])
                self.assertIn(avg, p.stdout.splitlines()[3])
                self.assertIn('1000000', p.stdout)

    def test_invalid_files_in_both_modes(self):
        for path in sorted((DATA / 'invalid').glob('*.json')):
            for mode, args in [('generate', ['10']), ('prob', ['10', 'a'])]:
                with self.subTest(file=path.name, mode=mode):
                    p = self.cli('task11', mode, path, *args)
                    self.assertEqual(p.returncode, 2, p.stderr)
                    self.assertIn('error:', p.stderr)
                    self.assertNotIn('Traceback', p.stderr)

    def test_oversized_json_integer(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'large.json'
            path.write_text('{"depth":' + '1' * 5000 + '}')
            p = self.cli('task11', 'generate', path, 10)
            self.assertEqual(p.returncode, 2, p.stderr)
            self.assertNotIn('Traceback', p.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
# End OpenAI Codex generated code.
