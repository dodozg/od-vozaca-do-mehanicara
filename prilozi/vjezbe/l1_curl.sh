#!/usr/bin/env bash
# L1: OpenAI-kompatibilni API. Tijelo zahtjeva šaljemo iz UTF-8 datoteke:
# curl s -d "...č..." u Windows ljusci pokvari dijakritike i poslužitelj vrati 400.
PY="venv/Scripts/python -X utf8"
G=models/gemma-4-E2B-it-GGUF/gemma-4-E2B-it-Q4_K_M.gguf
Z=logovi/z_upit.json
cat > $Z <<'JSON'
{"model":"gemma","seed":1,"max_tokens":128,"messages":[{"role":"user","content":"Objasni u tri rečenice zašto perilica rublja ne izbacuje vodu i što prvo treba provjeriti."}]}
JSON
$PY skripte/mjeri.py logovi/l1_server2.txt -- llama/llama-server.exe -m $G -c 4096 -t 4 --port 8080 --host 127.0.0.1 --reasoning off &
until curl -s http://127.0.0.1:8080/health | grep -q ok; do sleep 1; done
{
echo "### POST /v1/chat/completions, tijelo iz datoteke"
curl -s http://127.0.0.1:8080/v1/chat/completions -H "Content-Type: application/json" --data-binary @$Z; echo
echo "### isti upit drugi put (prompt cache)"
curl -s http://127.0.0.1:8080/v1/chat/completions -H "Content-Type: application/json" --data-binary @$Z; echo
} > logovi/l1_curl2.txt 2>&1
taskkill //IM llama-server.exe //F > /dev/null
wait
