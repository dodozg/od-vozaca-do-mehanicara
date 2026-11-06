#!/usr/bin/env bash
# L10: pokušaj Mergekita. Zasebno okruženje da glavni venv ostane netaknut.
LOG=logovi/l10_mergekit.txt
PY312="$(py -0p 2>/dev/null | grep -E '3\.1[0-3]' | head -1 | awk '{print $NF}')"
echo "### dostupni pythoni:" >> $LOG; py -0p >> $LOG 2>&1
venv/Scripts/python -m venv models/venv_mk >> $LOG 2>&1
echo "### pip install mergekit (puna instalacija, Python 3.14)" >> $LOG
timeout 300 models/venv_mk/Scripts/python -m pip install mergekit >> $LOG 2>&1; echo "exit=$?" >> $LOG
echo "### pip install --no-deps mergekit" >> $LOG
models/venv_mk/Scripts/python -m pip install --no-deps mergekit >> $LOG 2>&1; echo "exit=$?" >> $LOG
SP="$(cygpath -w "$PWD/venv/Lib/site-packages")"
echo "### mergekit-yaml --help, s paketima glavnog venva" >> $LOG
PYTHONPATH="$SP" PYTHONUTF8=1 models/venv_mk/Scripts/mergekit-yaml --help >> $LOG 2>&1; echo "exit=$?" >> $LOG
