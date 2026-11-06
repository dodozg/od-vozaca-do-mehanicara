#!/usr/bin/env bash
# L1: prva vožnja. llama-cli s oba kandidata, zatim llama-completion za detaljna vremena.
# Pokretanje iz korijena vježbi (mape u kojoj su llama/, models/, skripte/, logovi/).
PY="venv/Scripts/python -X utf8"
G=models/gemma-4-E2B-it-GGUF/gemma-4-E2B-it-Q4_K_M.gguf
Q=models/Qwen3-4B-GGUF/Qwen3-4B-Q4_K_M.gguf
P1="Objasni u tri rečenice zašto perilica rublja ne izbacuje vodu i što prvo treba provjeriti."
P2="Napiši kratku, pristojnu poruku stranci da serviser dolazi u četvrtak između 9 i 11 sati i da treba osigurati pristup perilici posuđa."
P3="Sažmi u jednoj rečenici: Tehničar je došao u utorak, pregledao hladnjak i utvrdio da kompresor ne radi. Dio je naručen i stiže za pet dana, a stranka je pristala pričekati."
for ime in gemma qwen; do
  [ $ime = gemma ] && M=$G || M=$Q
  L=logovi/l1_${ime}_cli.txt
  # zadano ponašanje, razmišljanje uključeno ako ga predložak ima
  if [ $ime = qwen ]; then $PY skripte/mjeri.py $L -- llama/llama-cli.exe -m $M -p "$P1" -st -n 256 -c 4096 -t 4 --perf --seed 1; fi
  # razmišljanje isključeno, tri hrvatska prompta
  i=1
  for P in "$P1" "$P2" "$P3"; do
    $PY skripte/mjeri.py logovi/l1_${ime}_cli_bez_razmisljanja.txt -- llama/llama-cli.exe -m $M -p "$P" -st -n 256 -c 4096 -t 4 --perf --seed 1 -rea off
    i=$((i+1))
  done
done
