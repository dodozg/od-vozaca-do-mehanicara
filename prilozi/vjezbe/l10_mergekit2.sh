#!/usr/bin/env bash
# L10: Mergekit na Pythonu 3.14 bez prevođenja immutables.
# immutables ima i čistu Python inačicu (map.py), pa je dovoljno izvorni kod staviti na PYTHONPATH.
LOG=logovi/l10_mergekit.txt
V=models/venv_mk/Scripts
echo "### pip download immutables (sdist), raspakirati, koristiti pure-Python map.py" >> $LOG
mkdir -p models/mk_dep
venv/Scripts/python -m pip download immutables==0.21 --no-deps --no-binary :all: --no-build-isolation -d models/mk_dep >> $LOG 2>&1
tar -xzf models/mk_dep/immutables-0.21.tar.gz -C models/mk_dep immutables-0.21/immutables >> $LOG 2>&1
ls models/mk_dep/immutables-0.21/immutables >> $LOG 2>&1
SP="$(cygpath -w "$PWD/venv/Lib/site-packages")"; IM="$(cygpath -w "$PWD/models/mk_dep/immutables-0.21")"
export PYTHONPATH="$IM;$SP" PYTHONUTF8=1
echo "### mergekit-yaml --help" >> $LOG
$V/mergekit-yaml --help > logovi/l10_mergekit_help.txt 2>&1
mkdir -p models/l10/mk
cat > models/l10/mk/linear.yml <<'YML'
merge_method: linear
dtype: float16
models:
  - model: models/l9/spojeno
    parameters: {weight: 0.5}
  - model: models/l9/spojeno_prenaucen
    parameters: {weight: 0.5}
tokenizer_source: base
YML
cat > models/l10/mk/dare.yml <<'YML'
merge_method: dare_ties
base_model: models/SmolLM2-135M-Instruct
dtype: float16
models:
  - model: models/l9/spojeno
    parameters: {weight: 1.0}
  - model: models/l9/spojeno_prenaucen
    parameters: {weight: 1.0}
parameters: {k: 0.3}
tokenizer_source: base
YML
for N in linear dare; do
  echo "### mergekit-yaml $N" >> $LOG
  T0=$(date +%s)
  $V/mergekit-yaml models/l10/mk/$N.yml models/l10/mk/izlaz_$N --lazy-unpickle >> $LOG 2>&1; echo "exit=$? trajanje=$(( $(date +%s)-T0 )) s" >> $LOG
  ls -la models/l10/mk/izlaz_$N >> $LOG 2>&1
done
