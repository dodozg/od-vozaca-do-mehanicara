#!/usr/bin/env bash
# Redoslijed preostalih vježbi, jedna po jedna da se mjerenja ne ometaju.
PY="venv/Scripts/python -X utf8"
G=models/gemma-4-E2B-it-GGUF/gemma-4-E2B-it-Q4_K_M.gguf
until grep -q "#MJERI" logovi/l9_prenaucen.txt; do sleep 5; done
cp models/l9/prenaucen/gubitak.csv grafovi/gubitak_prenaucen.csv
date; bash skripte/l9_lanac.sh
date; rm -f logovi/l10.txt; $PY skripte/l10_kirurgija.py models/SmolLM2-135M-Instruct models/l10 > logovi/l10.txt 2>&1
date; bash skripte/l10_mergekit.sh
date; $PY skripte/l8_tocnost.py $G "Gemma-4-E2B-Q4_K_M" podaci logovi/l8_server.txt grafovi/tocnost_zlatni.csv --no-rea > logovi/l8.txt 2>&1
date; $PY skripte/l11_opterecenje.py $G logovi/l11_server.txt grafovi/opterecenje.csv > logovi/l11.txt 2>&1
date; $PY skripte/l12_rag.py $G models/bge-m3-Q8_0-GGUF/bge-m3-q8_0.gguf models/granite-embedding-107m-multilingual-GGUF/granite-embedding-107m-multilingual-Q8_0.gguf podaci/kvaka_prirucnik.md logovi/l12_server.txt > logovi/l12.txt 2>&1
date; $PY skripte/mjeri.py logovi/l6_imatrix.txt -- llama/llama-imatrix.exe -m models/smol3/SmolLM3-Q8_0.gguf -f models/tekst/kal_mix.txt -o models/smol3/imatrix.gguf -t 4 -c 512 -b 512 --no-ppl
$PY skripte/l6_kvantizacija.py quant models/smol3/SmolLM3-F16.gguf models/smol3 logovi/l6_quant.txt grafovi/kvantizacija_velicina.csv Q4_K_M:models/smol3/imatrix.gguf Q3_K_M:models/smol3/imatrix.gguf >> logovi/l6_quant_sazetak.txt 2>&1
for T in Q8_0 Q4_K_M Q4_K_M-imat Q3_K_M Q3_K_M-imat Q2_K Q5_K_M Q6_K F16; do
  date; for J in hr en; do $PY skripte/l6_kvantizacija.py ppl models/smol3 logovi/l6_ppl.txt grafovi/kvantizacija_ppl.csv models/tekst/ppl_${J}_krat.txt $J $T >> logovi/l6_ppl_sazetak.txt 2>&1; done
done
date; echo SVE_GOTOVO
