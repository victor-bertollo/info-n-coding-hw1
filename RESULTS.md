# RESULTS

Вывод программы на собственных тестах. Сгенерировано `bash tests/run_tests.sh`.

#### Вариант

```
$ main.py --variant
variant: s = 3
k = 5, M = 2, L = 6, d = 1, q = 7, eps = 1/100
[exit code: 0]
```

## Задача 1.1

### Режим 1: реализация источника

#### variant.json, N = 100

```
$ main.py task11 generate tests/task11/variant.json 100 --seed 3
cccaccddcaeadbccbddccdcdabdadceadeaaecaceaebceeceecceeecacaaacbcecedbcdcecceccbcdaccedaeccecaeebecbc
[exit code: 0]
```

#### variant.json, N = 100, тот же seed (воспроизводимость)

```
$ main.py task11 generate tests/task11/variant.json 100 --seed 3
cccaccddcaeadbccbddccdcdabdadceadeaaecaceaebceeceecceeecacaaacbcecedbcdcecceccbcdaccedaeccecaeebecbc
[exit code: 0]
```

#### variant.json, N = 100, другой seed

```
$ main.py task11 generate tests/task11/variant.json 100 --seed 4
cbaeccaaaaccceeabcdcbebeabbaedebecbacbdecaecdcdbbbccaedbacedcecbccebccabcbeeaaacdcdcecdcadbacbedcbac
[exit code: 0]
```

#### variant.json, N = None (до прерывания)

```
$ main.py task11 generate tests/task11/variant.json None --seed 3    # SIGINT (Ctrl+C) через 1 с
первые 80 символов: cccaccddcaeadbccbddccdcdabdadceadeaaecaceaebceeceecceeecacaaacbcecedbcdcecceccbc
всего выведено байт: 2625422
[exit code: 130]
```

#### variant.json, N = 0 (по заданию тоже до прерывания)

```
$ main.py task11 generate tests/task11/variant.json 0 --seed 3    # SIGINT (Ctrl+C) через 1 с
первые 80 символов: cccaccddcaeadbccbddccdcdabdadceadeaaecaceaebceeceecceeecacaaacbcecedbcdcecceccbc
всего выведено байт: 2889698
[exit code: 130]
```

#### example2.json (пример 2 методички), N = 40

```
$ main.py task11 generate tests/task11/example2.json 40 --seed 3
0110111001011010010110110010110100110010
[exit code: 0]
```

### Режим 2: точные вероятности и частотная оценка

#### variant.json, блок e

```
$ main.py task11 prob tests/task11/variant.json 1000 e --seed 3
source: tests/task11/variant.json (L = 6, alphabet: a b c d e)
block: e (r = 1), seed = 3
(1) Pr{X_1..X_r = block}: 4313/13600 ≈ 0.317132
(2) period average:       6091/27200 ≈ 0.223934
(3) frequency, N = 1000: 113/500 ≈ 0.226000

        N   frequency   |f - (1)|   |f - (2)|
      100    0.230000    0.087132    0.006066
     1000    0.226000    0.091132    0.002066
    10000    0.214700    0.102432    0.009234
   100000    0.223590    0.093542    0.000344
  1000000    0.223957    0.093175    0.000023
[exit code: 0]
```

#### variant.json, блок c

```
$ main.py task11 prob tests/task11/variant.json 1000 c --seed 3
source: tests/task11/variant.json (L = 6, alphabet: a b c d e)
block: c (r = 1), seed = 3
(1) Pr{X_1..X_r = block}: 3827/13600 ≈ 0.281397
(2) period average:       8889/27200 ≈ 0.326801
(3) frequency, N = 1000: 33/100 ≈ 0.330000

        N   frequency   |f - (1)|   |f - (2)|
      100    0.370000    0.088603    0.043199
     1000    0.330000    0.048603    0.003199
    10000    0.341200    0.059803    0.014399
   100000    0.329220    0.047823    0.002419
  1000000    0.326933    0.045536    0.000132
[exit code: 0]
```

#### variant.json, блок c a e

```
$ main.py task11 prob tests/task11/variant.json 1000 c a e --seed 3
source: tests/task11/variant.json (L = 6, alphabet: a b c d e)
block: cae (r = 3), seed = 3
(1) Pr{X_1..X_r = block}: 574972307/62886400000 ≈ 0.009143
(2) period average:       12766567099/754636800000 ≈ 0.016917
(3) frequency, N = 1000: 9/499 ≈ 0.018036

        N   frequency   |f - (1)|   |f - (2)|
      100    0.020408    0.011265    0.003491
     1000    0.018036    0.008893    0.001119
    10000    0.015703    0.006560    0.001214
   100000    0.016810    0.007667    0.000107
  1000000    0.016768    0.007625    0.000149
[exit code: 0]
```

#### example2.json, блок 0 0 (сверка с ручным счётом: 17/60 и 527/1800)

```
$ main.py task11 prob tests/task11/example2.json 1000 0 0 --seed 3
source: tests/task11/example2.json (L = 4, alphabet: 0 1)
block: 00 (r = 2), seed = 3
(1) Pr{X_1..X_r = block}: 17/60 ≈ 0.283333
(2) period average:       527/1800 ≈ 0.292778
(3) frequency, N = 1000: 272/999 ≈ 0.272272

        N   frequency   |f - (1)|   |f - (2)|
      100    0.111111    0.172222    0.181667
     1000    0.272272    0.011061    0.020506
    10000    0.288229    0.004895    0.004549
   100000    0.291993    0.008660    0.000785
  1000000    0.293273    0.009940    0.000496
[exit code: 0]
```

### Вырожденные входы

#### один символ с вероятностью 1

```
$ main.py task11 prob tests/task11/degenerate/one_symbol.json 100 x x
source: tests/task11/degenerate/one_symbol.json (L = 1, alphabet: x)
block: xx (r = 2), seed = 0
(1) Pr{X_1..X_r = block}: 1 ≈ 1.000000
(2) period average:       1 ≈ 1.000000
(3) frequency, N = 100: 1 ≈ 1.000000

        N   frequency   |f - (1)|   |f - (2)|
      100    1.000000    0.000000    0.000000
     1000    1.000000    0.000000    0.000000
    10000    1.000000    0.000000    0.000000
   100000    1.000000    0.000000    0.000000
  1000000    1.000000    0.000000    0.000000
[exit code: 0]
```

#### source длины 1: обе точные величины совпадают

```
$ main.py task11 prob tests/task11/degenerate/length_one.json 1000 e --seed 3
source: tests/task11/degenerate/length_one.json (L = 1, alphabet: a b c d e)
block: e (r = 1), seed = 3
(1) Pr{X_1..X_r = block}: 4313/13600 ≈ 0.317132
(2) period average:       4313/13600 ≈ 0.317132
(3) frequency, N = 1000: 161/500 ≈ 0.322000

        N   frequency   |f - (1)|   |f - (2)|
      100    0.390000    0.072868    0.072868
     1000    0.322000    0.004868    0.004868
    10000    0.300400    0.016732    0.016732
   100000    0.316230    0.000902    0.000902
  1000000    0.316933    0.000199    0.000199
[exit code: 0]
```

#### нулевые вероятности: символ b не выпадает

```
$ main.py task11 generate tests/task11/degenerate/zero_probs.json 60 --seed 3
caceaaecaceceaaceaaaacacecceeaeaaceaccceeceacacaeaaccaaccaea
[exit code: 0]
```

#### нулевые вероятности: вероятность блока с b равна 0

```
$ main.py task11 prob tests/task11/degenerate/zero_probs.json 1000 b --seed 3
source: tests/task11/degenerate/zero_probs.json (L = 6, alphabet: a b c d e)
block: b (r = 1), seed = 3
(1) Pr{X_1..X_r = block}: 0 ≈ 0.000000
(2) period average:       0 ≈ 0.000000
(3) frequency, N = 1000: 0 ≈ 0.000000

        N   frequency   |f - (1)|   |f - (2)|
      100    0.000000    0.000000    0.000000
     1000    0.000000    0.000000    0.000000
    10000    0.000000    0.000000    0.000000
   100000    0.000000    0.000000    0.000000
  1000000    0.000000    0.000000    0.000000
[exit code: 0]
```

#### многобуквенные символы

```
$ main.py task11 generate tests/task11/degenerate/words.json 10 --seed 3
орёл решка орёл орёл решка решка орёл решка орёл орёл
[exit code: 0]
```

#### многобуквенные символы, режим 2

```
$ main.py task11 prob tests/task11/degenerate/words.json 1000 орёл орёл --seed 3
source: tests/task11/degenerate/words.json (L = 2, alphabet: орёл решка)
block: орёл орёл (r = 2), seed = 3
(1) Pr{X_1..X_r = block}: 9/20 ≈ 0.450000
(2) period average:       9/20 ≈ 0.450000
(3) frequency, N = 1000: 421/999 ≈ 0.421421

        N   frequency   |f - (1)|   |f - (2)|
      100    0.414141    0.035859    0.035859
     1000    0.421421    0.028579    0.028579
    10000    0.450345    0.000345    0.000345
   100000    0.452095    0.002095    0.002095
  1000000    0.449329    0.000671    0.000671
[exit code: 0]
```

#### дроби и десятичная запись вперемешку, пробелы

```
$ main.py task11 prob tests/task11/degenerate/mixed_notation.json 1000 a --seed 3
source: tests/task11/degenerate/mixed_notation.json (L = 6, alphabet: a b c d e)
block: a (r = 1), seed = 3
(1) Pr{X_1..X_r = block}: 29/136 ≈ 0.213235
(2) period average:       29/136 ≈ 0.213235
(3) frequency, N = 1000: 9/40 ≈ 0.225000

        N   frequency   |f - (1)|   |f - (2)|
      100    0.230000    0.016765    0.016765
     1000    0.225000    0.011765    0.011765
    10000    0.206800    0.006435    0.006435
   100000    0.213620    0.000385    0.000385
  1000000    0.212669    0.000566    0.000566
[exit code: 0]
```

#### N = 1, блок длины 1

```
$ main.py task11 prob tests/task11/variant.json 1 a --seed 3
source: tests/task11/variant.json (L = 6, alphabet: a b c d e)
block: a (r = 1), seed = 3
(1) Pr{X_1..X_r = block}: 273/1360 ≈ 0.200735
(2) period average:       611/2720 ≈ 0.224632
(3) frequency, N = 1: 0 ≈ 0.000000

        N   frequency   |f - (1)|   |f - (2)|
      100    0.170000    0.030735    0.054632
     1000    0.217000    0.016265    0.007632
    10000    0.220400    0.019665    0.004232
   100000    0.223590    0.022855    0.001042
  1000000    0.224589    0.023854    0.000043
[exit code: 0]
```

#### N = r: ровно одно окно

```
$ main.py task11 prob tests/task11/variant.json 3 c a e --seed 3
source: tests/task11/variant.json (L = 6, alphabet: a b c d e)
block: cae (r = 3), seed = 3
(1) Pr{X_1..X_r = block}: 574972307/62886400000 ≈ 0.009143
(2) period average:       12766567099/754636800000 ≈ 0.016917
(3) frequency, N = 3: 0 ≈ 0.000000

        N   frequency   |f - (1)|   |f - (2)|
      100    0.020408    0.011265    0.003491
     1000    0.018036    0.008893    0.001119
    10000    0.015703    0.006560    0.001214
   100000    0.016810    0.007667    0.000107
  1000000    0.016768    0.007625    0.000149
[exit code: 0]
```

### Некорректные входы: файл описания

#### empty_model.json

```
$ main.py task11 generate tests/task11/invalid/empty_model.json 10
error: models['model1'] must be non-empty dict
[exit code: 2]
```

#### empty_source.json

```
$ main.py task11 generate tests/task11/invalid/empty_source.json 10
error: "source" must be non-empty list
[exit code: 2]
```

#### garbage_prob.json

```
$ main.py task11 generate tests/task11/invalid/garbage_prob.json 10
error: failed to parse models['model1']['a'] as fraction
[exit code: 2]
```

#### missing_field.json

```
$ main.py task11 generate tests/task11/invalid/missing_field.json 10
error: data has no key switches
[exit code: 2]
```

#### negative.json

```
$ main.py task11 generate tests/task11/invalid/negative.json 10
error: models['model1']['a'] can't be less than 0
[exit code: 2]
```

#### not_normalized.json

```
$ main.py task11 generate tests/task11/invalid/not_normalized.json 10
error: sum of models['model1'] should be equal to 1, got 9/8
[exit code: 2]
```

#### not_utf8.json

```
$ main.py task11 generate tests/task11/invalid/not_utf8.json 10
error: file tests/task11/invalid/not_utf8.json not in UTF-8
[exit code: 2]
```

#### number_prob.json

```
$ main.py task11 generate tests/task11/invalid/number_prob.json 10
error: models['model1']['a'] must be str object
[exit code: 2]
```

#### root_list.json

```
$ main.py task11 generate tests/task11/invalid/root_list.json 10
error: data is not a dict
[exit code: 2]
```

#### source_not_list.json

```
$ main.py task11 generate tests/task11/invalid/source_not_list.json 10
error: "source" must be non-empty list
[exit code: 2]
```

#### truncated.json

```
$ main.py task11 generate tests/task11/invalid/truncated.json 10
error: file tests/task11/invalid/truncated.json content is not a valid json
[exit code: 2]
```

#### unknown_model.json

```
$ main.py task11 generate tests/task11/invalid/unknown_model.json 10
error: model3 model doesn't exist
[exit code: 2]
```

#### unknown_switch.json

```
$ main.py task11 generate tests/task11/invalid/unknown_switch.json 10
error: s3 switch doesn't exist
[exit code: 2]
```

#### zero_denominator.json

```
$ main.py task11 generate tests/task11/invalid/zero_denominator.json 10
error: failed to parse models['model1']['a'] as fraction
[exit code: 2]
```

#### файла нет

```
$ main.py task11 generate tests/task11/invalid/no_such_file.json 10
error: failed to open file tests/task11/invalid/no_such_file.json: No such file or directory
[exit code: 2]
```

#### каталог вместо файла

```
$ main.py task11 generate tests/task11/invalid 10
error: failed to open file tests/task11/invalid: Is a directory
[exit code: 2]
```

### Некорректные входы: аргументы

#### N не число

```
$ main.py task11 generate tests/task11/variant.json abc
usage: main.py task11 generate [-h] [--seed SEED] source N
main.py task11 generate: error: argument N: expected integer or None, got 'abc'
[exit code: 2]
```

#### режим 2, N = 0

```
$ main.py task11 prob tests/task11/variant.json 0 a
usage: main.py task11 prob [-h] [--seed SEED] source N SYMBOL [SYMBOL ...]
main.py task11 prob: error: argument N: expected positive integer, got 0
[exit code: 2]
```

#### режим 2, N < 0

```
$ main.py task11 prob tests/task11/variant.json -5 a
usage: main.py task11 prob [-h] [--seed SEED] source N SYMBOL [SYMBOL ...]
main.py task11 prob: error: argument N: expected positive integer, got -5
[exit code: 2]
```

#### режим 2, символ не из алфавита

```
$ main.py task11 prob tests/task11/variant.json 100 z
error: symbols ['z'] are not in source alphabet ['a', 'b', 'c', 'd', 'e']
[exit code: 2]
```

#### режим 2, длина блока больше N

```
$ main.py task11 prob tests/task11/variant.json 2 a b c
error: block length r = 3 exceeds N = 2
[exit code: 2]
```

#### режим 2, нет блока

```
$ main.py task11 prob tests/task11/variant.json 100
usage: main.py task11 prob [-h] [--seed SEED] source N SYMBOL [SYMBOL ...]
main.py task11 prob: error: the following arguments are required: SYMBOL
[exit code: 2]
```

#### seed не число

```
$ main.py task11 generate tests/task11/variant.json 10 --seed abc
usage: main.py task11 generate [-h] [--seed SEED] source N
main.py task11 generate: error: argument --seed: invalid int value: 'abc'
[exit code: 2]
```

#### нет режима

```
$ main.py task11
usage: main.py task11 [-h] {generate,prob} ...
main.py task11: error: the following arguments are required: mode
[exit code: 2]
```

