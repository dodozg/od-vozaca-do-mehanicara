#!/usr/bin/env bash
# L10: zasebno okruženje za Mergekit, da glavni venv ostane netaknut.
# Puna instalacija (pip install mergekit) na Pythonu 3.14 pada na prevođenju paketa immutables; vidi mjerenja.md.
LOG=logovi/l10_mergekit.txt
venv/Scripts/python -m venv models/venv_mk >> $LOG 2>&1
echo "### pip install --no-deps, točne inačice" >> $LOG
models/venv_mk/Scripts/python -m pip install --no-deps -r okruzenje/requirements-mergekit.txt >> $LOG 2>&1; echo "exit=$?" >> $LOG
