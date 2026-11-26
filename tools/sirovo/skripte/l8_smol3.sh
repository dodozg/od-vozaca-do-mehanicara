#!/bin/bash
# L8 na SmolLM3: iste postavke kao za Gemmu (glavni_lanac.sh), tri razine jedna za drugom.
cd /d/llm-vjezbe
for R in Q8_0 Q4_K_M Q2_K; do
  echo "#START $R $(date '+%Y-%m-%d %H:%M:%S')" >> logovi/l8_smol3_vrijeme.txt
  t0=$(date +%s)
  python -X utf8 skripte/l8_tocnost.py models/smol3/SmolLM3-$R.gguf "SmolLM3-$R" podaci \
    logovi/l8_smol3_${R}_server.txt grafovi/tocnost_zlatni_smol3.csv --no-rea --port 8095 > logovi/l8_smol3_$R.txt 2>&1
  echo "#KRAJ $R izlaz=$? trajanje=$(( $(date +%s) - t0 )) s $(date '+%Y-%m-%d %H:%M:%S')" >> logovi/l8_smol3_vrijeme.txt
done
