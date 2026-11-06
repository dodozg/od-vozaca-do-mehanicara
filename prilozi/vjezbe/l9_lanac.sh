#!/usr/bin/env bash
# L9: spajanje adaptera, pretvorba u GGUF, kvantizacija i provjera cijelog lanca.
PY="venv/Scripts/python -X utf8"
KRATKI="Iz zapisnika izvuci JSON s poljima uredaj, kvar, dio, hitnost."
S=models/l9/gguf; mkdir -p $S
$PY skripte/l9_spoji.py models/SmolLM2-135M-Instruct models/l9/glavni models/l9/spojeno > logovi/l9_spoji.txt 2>&1
$PY skripte/mjeri.py logovi/l9_convert.txt -- venv/Scripts/python.exe -X utf8 llama-src/llama.cpp-b12110/convert_hf_to_gguf.py models/l9/spojeno --outtype f16 --outfile $S/kvaka-F16.gguf
for T in Q8_0 Q4_K_M Q2_K; do $PY skripte/mjeri.py logovi/l9_quant.txt -- llama/llama-quantize.exe $S/kvaka-F16.gguf $S/kvaka-$T.gguf $T 4; done
ls -la $S > logovi/l9_gguf_velicine.txt
P="Stranka zove, hladnjak ne hladi, sumnja na kompresor. Treba odmah."
$PY skripte/mjeri.py logovi/l9_cli.txt -- llama/llama-cli.exe -m $S/kvaka-Q4_K_M.gguf -sys "$KRATKI" -p "$P" -st -n 80 -c 2048 -t 4 --temp 0 --seed 1
export KRATKI
$PY skripte/l8_tocnost.py $S/kvaka-Q4_K_M.gguf "LoRA-SmolLM2-Q4_K_M" podaci logovi/l9_tocnost_server.txt grafovi/tocnost_zlatni.csv --sustav-tekst "$KRATKI" --max 70 --port 8095 --ispis 3 >> logovi/l9_tocnost.txt 2>&1
for T in Q8_0 Q2_K; do
  $PY skripte/l8_tocnost.py $S/kvaka-$T.gguf "LoRA-SmolLM2-$T" podaci logovi/l9_tocnost_server.txt grafovi/tocnost_zlatni.csv --sustav-tekst "$KRATKI" --max 70 --port 8095 --ispis 2 --nacini shema >> logovi/l9_tocnost.txt 2>&1
done
# bazni model bez treninga kroz isti GGUF put, da usporedba bude poštena
$PY skripte/mjeri.py logovi/l9_convert.txt -- venv/Scripts/python.exe -X utf8 llama-src/llama.cpp-b12110/convert_hf_to_gguf.py models/SmolLM2-135M-Instruct --outtype f16 --outfile $S/baza-F16.gguf
$PY skripte/l8_tocnost.py $S/baza-F16.gguf "baza-SmolLM2-F16" podaci logovi/l9_tocnost_server.txt grafovi/tocnost_zlatni.csv --sustav-tekst "$KRATKI" --max 70 --port 8095 --ispis 3 --nacini shema >> logovi/l9_tocnost.txt 2>&1
# adapter izravno, bez spajanja
$PY skripte/mjeri.py logovi/l9_lora_gguf.txt -- venv/Scripts/python.exe -X utf8 llama-src/llama.cpp-b12110/convert_lora_to_gguf.py models/l9/glavni --base models/SmolLM2-135M-Instruct --outfile $S/adapter.gguf --outtype f16
$PY skripte/mjeri.py logovi/l9_lora_gguf.txt -- llama/llama-cli.exe -m $S/baza-F16.gguf --lora $S/adapter.gguf -sys "$KRATKI" -p "$P" -st -n 80 -c 2048 -t 4 --temp 0 --seed 1
# drugi spojeni model (prenaučeni), treba za Mergekit
$PY skripte/l9_spoji.py models/SmolLM2-135M-Instruct models/l9/prenaucen models/l9/spojeno_prenaucen >> logovi/l9_spoji.txt 2>&1
