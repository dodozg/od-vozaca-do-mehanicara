#!/usr/bin/env bash
# L1 drugi dio: detaljna vremena s llama-completion i test OpenAI-kompatibilnog API-ja curlom.
PY="venv/Scripts/python -X utf8"
G=models/gemma-4-E2B-it-GGUF/gemma-4-E2B-it-Q4_K_M.gguf
Q=models/Qwen3-4B-GGUF/Qwen3-4B-Q4_K_M.gguf
P="Objasni u tri rečenice zašto perilica rublja ne izbacuje vodu i što prvo treba provjeriti."

# llama-completion: stari "sirovi" alat, ispisuje load time, prompt eval, eval
for ime in gemma qwen; do
  [ $ime = gemma ] && M=$G || M=$Q
  $PY skripte/mjeri.py logovi/l1_${ime}_completion.txt -- llama/llama-completion.exe -m $M -no-cnv -p "$P" -n 128 -c 4096 -t 4 --perf --seed 1 --no-display-prompt
done

# llama-server
$PY skripte/mjeri.py logovi/l1_server.txt -- llama/llama-server.exe -m $G -c 4096 -t 4 --port 8080 --host 127.0.0.1 --reasoning off &
until curl -s http://127.0.0.1:8080/health | grep -q ok; do sleep 1; done
{
echo "### GET /health"; curl -s http://127.0.0.1:8080/health; echo
echo "### GET /v1/models"; curl -s http://127.0.0.1:8080/v1/models; echo
echo "### POST /v1/chat/completions"
curl -s http://127.0.0.1:8080/v1/chat/completions -H "Content-Type: application/json" -d "{\"model\":\"gemma\",\"seed\":1,\"max_tokens\":128,\"messages\":[{\"role\":\"user\",\"content\":\"$P\"}]}"; echo
echo "### POST /v1/chat/completions isti prompt drugi put (prompt cache)"
curl -s http://127.0.0.1:8080/v1/chat/completions -H "Content-Type: application/json" -d "{\"model\":\"gemma\",\"seed\":2,\"max_tokens\":64,\"messages\":[{\"role\":\"user\",\"content\":\"$P\"}]}"; echo
echo "### POST /v1/chat/completions stream=true (prvih 8 redaka)"
curl -sN http://127.0.0.1:8080/v1/chat/completions -H "Content-Type: application/json" -d "{\"model\":\"gemma\",\"stream\":true,\"max_tokens\":8,\"messages\":[{\"role\":\"user\",\"content\":\"Reci dobar dan.\"}]}" | head -8
} > logovi/l1_curl.txt 2>&1
taskkill //IM llama-server.exe //F > /dev/null
wait
