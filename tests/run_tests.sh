#!/usr/bin/env bash
# Begin Claude generated code, adapted by OpenAI Codex; see SOURCES.md.

cd "$(dirname "$0")/.." || exit 1
PY=${PYTHON:-$(uv run --quiet python -c 'import sys; print(sys.executable)')} || exit 1
OUT=RESULTS.md
T=tests/task11
# Begin OpenAI Codex changes: validate expected exit codes.
failures=0
EXPECTED_CODE=0
# End OpenAI Codex changes.

run() {
    local title=$1
    shift
    {
        echo "#### $title"
        echo
        echo '```'
        echo "\$ main.py $*"
        # Begin OpenAI Codex changes: detect failed test runs.
        "$PY" src/main.py "$@" 2>&1
        local code=$?
        echo "[exit code: $code]"
        if [ "$code" -ne "$EXPECTED_CODE" ]; then
            echo "FAIL: expected exit code $EXPECTED_CODE"
            failures=$((failures + 1))
        fi
        # End OpenAI Codex changes.
        echo '```'
        echo
    } >> "$OUT"
}

run_interrupted() {
    local title=$1
    shift
    local tmp
    tmp=$(mktemp)
    # запуск не через "&": фоновые процессы неинтерактивного bash игнорируют SIGINT
    timeout --preserve-status -s INT 1 $PY src/main.py "$@" > "$tmp" 2>&1
    local code=$?
    # Begin OpenAI Codex changes: validate interrupt handling.
    if [ "$code" -ne 130 ]; then
        failures=$((failures + 1))
    fi
    # End OpenAI Codex changes.
    {
        echo "#### $title"
        echo
        echo '```'
        echo "\$ main.py $*    # SIGINT (Ctrl+C) через 1 с"
        echo "первые 80 символов: $(head -c 80 "$tmp")"
        echo "всего выведено байт: $(wc -c < "$tmp")"
        echo "[exit code: $code]"
        echo '```'
        echo
    } >> "$OUT"
    rm -f "$tmp"
}

{
    echo "# RESULTS"
    echo
    echo "Вывод программы на собственных тестах. Сгенерировано \`bash tests/run_tests.sh\`."
    echo
} > "$OUT"

run "Вариант" --variant

echo "## Задача 1.1" >> "$OUT"
echo >> "$OUT"

echo "### Режим 1: реализация источника" >> "$OUT"
echo >> "$OUT"
run "variant.json, N = 100" task11 generate $T/variant.json 100 --seed 3
run "variant.json, N = 100, тот же seed (воспроизводимость)" task11 generate $T/variant.json 100 --seed 3
run "variant.json, N = 100, другой seed" task11 generate $T/variant.json 100 --seed 4
run_interrupted "variant.json, N = None (до прерывания)" task11 generate $T/variant.json None --seed 3
run_interrupted "variant.json, N = 0 (по заданию тоже до прерывания)" task11 generate $T/variant.json 0 --seed 3
run "example2.json (пример 2 методички), N = 40" task11 generate $T/example2.json 40 --seed 3

echo "### Режим 2: точные вероятности и частотная оценка" >> "$OUT"
echo >> "$OUT"
run "variant.json, блок e" task11 prob $T/variant.json 1000 e --seed 3
run "variant.json, блок c" task11 prob $T/variant.json 1000 c --seed 3
run "variant.json, блок c a e" task11 prob $T/variant.json 1000 c a e --seed 3
run "example2.json, блок 0 0 (сверка с ручным счётом: 17/60 и 527/1800)" task11 prob $T/example2.json 1000 0 0 --seed 3

echo "### Вырожденные входы" >> "$OUT"
echo >> "$OUT"
run "один символ с вероятностью 1" task11 prob $T/degenerate/one_symbol.json 100 x x
run "source длины 1: обе точные величины совпадают" task11 prob $T/degenerate/length_one.json 1000 e --seed 3
run "нулевые вероятности: символ b не выпадает" task11 generate $T/degenerate/zero_probs.json 60 --seed 3
run "нулевые вероятности: вероятность блока с b равна 0" task11 prob $T/degenerate/zero_probs.json 1000 b --seed 3
run "многобуквенные символы" task11 generate $T/degenerate/words.json 10 --seed 3
run "многобуквенные символы, режим 2" task11 prob $T/degenerate/words.json 1000 орёл орёл --seed 3
run "дроби и десятичная запись вперемешку, пробелы" task11 prob $T/degenerate/mixed_notation.json 1000 a --seed 3
run "N = 1, блок длины 1" task11 prob $T/variant.json 1 a --seed 3
run "N = r: ровно одно окно" task11 prob $T/variant.json 3 c a e --seed 3

EXPECTED_CODE=2
echo "### Некорректные входы: файл описания" >> "$OUT"
echo >> "$OUT"
for f in $T/invalid/*.json; do
    run "$(basename "$f")" task11 generate "$f" 10
done
run "файла нет" task11 generate $T/invalid/no_such_file.json 10
run "каталог вместо файла" task11 generate $T/invalid 10

echo "### Некорректные входы: аргументы" >> "$OUT"
echo >> "$OUT"
run "N не число" task11 generate $T/variant.json abc
run "режим 2, N = 0" task11 prob $T/variant.json 0 a
run "режим 2, N < 0" task11 prob $T/variant.json -5 a
run "режим 2, символ не из алфавита" task11 prob $T/variant.json 100 z
run "режим 2, длина блока больше N" task11 prob $T/variant.json 2 a b c
run "режим 2, нет блока" task11 prob $T/variant.json 100
run "seed не число" task11 generate $T/variant.json 10 --seed abc
run "нет режима" task11

# Begin OpenAI Codex changes: extended source tests and mathematical checks.
EXPECTED_CODE=0
echo '### Расширенный формат' >> "$OUT"
for f in markov markov_stationary markov_absorption mixture mixture_nested stationary; do
    run "$f, generate" task11 generate "$T/$f.json" 30 --seed 3
    run "$f, prob(a)" task11 prob "$T/$f.json" 1000 a --seed 3
done
run "markov, block ab" task11 prob "$T/markov.json" 1000 a b --seed 3
run "absorption, block bc" task11 prob "$T/markov_absorption.json" 1000 b c --seed 3
run "absorption, block de" task11 prob "$T/markov_absorption.json" 1000 d e --seed 3
run "mixture, another component" task11 prob "$T/mixture.json" 1000 a --seed 0
for f in markov_depth2 markov_single mixture_zero_weight; do
    run "$f, generate" task11 generate "$T/degenerate/$f.json" 30 --seed 3
done
run "depth two, block ab" task11 prob "$T/degenerate/markov_depth2.json" 1000 a b --seed 3
run "single-state Markov" task11 prob "$T/degenerate/markov_single.json" 100 x x --seed 3
run "zero mixture weight" task11 prob "$T/degenerate/mixture_zero_weight.json" 1000 a --seed 3
run_interrupted "negative N" task11 generate "$T/markov.json" -1 --seed 3
EXPECTED_CODE=2
for f in "$T"/invalid/*.json; do
    run "$(basename "$f"), prob" task11 prob "$f" 10 a
done
{
    echo '### Проверки математических свойств и CLI'
    echo '```'
    echo '$ python -m unittest discover -s tests -p test_*.py -v'
    "$PY" -m unittest discover -s tests -p 'test_*.py' -v 2>&1
    code=$?
    echo "[exit code: $code]"
    if [ "$code" -ne 0 ]; then
        failures=$((failures + 1))
    fi
    echo '```'
    echo
    echo "Unexpected failures: $failures"
} >> "$OUT"
echo "готово: $OUT; неожиданных ошибок: $failures"
if [ "$failures" -ne 0 ]; then
    exit 1
fi
# End OpenAI Codex changes.
# End Claude generated code, adapted by OpenAI Codex.
