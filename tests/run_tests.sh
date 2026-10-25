#!/usr/bin/env bash
# весь файл сгенерирован Claude (Anthropic), см. SOURCES.md
# Прогоняет тесты и пишет вывод программы в RESULTS.md.
# Запуск из корня репозитория: bash tests/run_tests.sh
# Интерпретатор можно переопределить: PYTHON=python3 bash tests/run_tests.sh

cd "$(dirname "$0")/.." || exit 1
# интерпретатор берётся из окружения uv один раз и дальше вызывается напрямую:
# через "uv run" сигнал SIGINT получил бы uv, а не программа
PY=${PYTHON:-$(uv run --quiet python -c 'import sys; print(sys.executable)')} || exit 1
OUT=RESULTS.md
T=tests/task11

run() {
    local title=$1
    shift
    {
        echo "#### $title"
        echo
        echo '```'
        echo "\$ main.py $*"
        $PY src/main.py "$@" 2>&1
        echo "[exit code: $?]"
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

echo "готово: $OUT"
