# Šalabahter

Naredbe su prepisane iz poglavlja, a broj u zagradi upućuje na objašnjenje. Mjerene su na izgradnji llama.cpp b12110, pa novije inačice mogu tražiti drukčije zastavice. U PowerShellu `\` na kraju retka zamijeni znakom `` ` ``, a `curl` piši `curl.exe`.

## Pokretanje

Jedno pitanje iz terminala (2):

```bash
./llama/llama-cli -m models/gemma-4-E2B-it-Q4_K_M.gguf \
  -st -n 256 -c 4096 -t 4 --perf --seed 1 -rea off \
  -p "Pitanje ovdje"
```

::: {.drugacije}
Isti argumenti izvedeni su iz Git Basha na Windowsu, a u PowerShellu, Linuxu i Macu nisu pokretani.
:::

Poslužitelj, samo na tvom računalu (2):

```bash
./llama/llama-server -m models/gemma-4-E2B-it-Q4_K_M.gguf \
  -c 4096 -t 4 --port 8080 --host 127.0.0.1 --reasoning off
```

Zahtjev, s tijelom iz UTF-8 datoteke (2):

```bash
curl -s http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" --data-binary "@upit.json"
```

Što je predložak napravio od poruka (5):

```bash
curl -s http://127.0.0.1:8080/apply-template \
  -H "Content-Type: application/json" --data-binary @poruke.json
```

Model na grafičkoj kartici (8):

```bash
llama-server -m model.gguf -c 8192 -ngl all --port 8080
```

::: {.neprovjereno}
Traži GPU.
:::

| Zastavica | Značenje | Pogl. |
|---|-----|-|
| `-c` | ukupan kontekst; `-np` ga dijeli na slotove | 8 |
| `-n`, `max_tokens` | najviše tokena odgovora | 2 |
| `-rea off`, `--reasoning off` | isključuje razmišljanje | 2, 5 |
| `--temp`, `--seed` | temperatura i sjeme | 6 |
| `--chat-template-file` | zamjenjuje predložak iz datoteke | 5, 10 |
| `--api-key` | obvezno prije otvaranja prema mreži | 2 |

::: {.neprovjereno}
`--api-key` preuzet je iz dokumentacije, bez pokretanja. `--chat-template-file` pokrenut je samo s pokusnim predlošcima iz poglavlja 5.
:::

Četiri korisnika po 8192 tokena traže `-c 32768 -np 4` (8).

## Pretvorba i kvantizacija

Iz Hugging Face mape u GGUF F16, skriptom iz izvornog koda iste oznake (11):

```bash
python -X utf8 llama-src/llama.cpp-b12110/convert_hf_to_gguf.py \
  models/SmolLM3-3B --outtype f16 \
  --outfile models/smol3/SmolLM3-F16.gguf
```

Pretvorba može izvršiti kod iz repozitorija. Nepoznat model pretvaraj u izoliranom okruženju (10, 11).

Kvantizacija, uvijek iz F16 ili BF16 (11). Zadnji argument je broj dretvi:

```bash
./llama/llama-quantize models/smol3/SmolLM3-F16.gguf \
  models/smol3/SmolLM3-Q4_K_M.gguf Q4_K_M 4
```

Isto s imatrixom (11):

```bash
./llama/llama-imatrix -m models/smol3/SmolLM3-Q8_0.gguf \
  -f models/tekst/kal_mix.txt -o models/smol3/imatrix.gguf \
  -t 4 -c 512 -b 512 --no-ppl
./llama/llama-quantize --imatrix models/smol3/imatrix.gguf \
  models/smol3/SmolLM3-F16.gguf \
  models/smol3/SmolLM3-Q4_K_M-imat.gguf Q4_K_M 4
```

LoRA adapter u GGUF i vožnja s njim (16):

```bash
python -X utf8 llama-src/llama.cpp-b12110/convert_lora_to_gguf.py \
  models/l9/glavni --base models/SmolLM2-135M-Instruct \
  --outfile models/l9/gguf/adapter.gguf --outtype f16
./llama/llama-cli -m models/l9/gguf/baza-F16.gguf \
  --lora models/l9/gguf/adapter.gguf -sys "$KRATKI" -p "$P" \
  -st -n 80 -c 2048 -t 4 --temp 0 --seed 1
```

## Mjerenje

Brzina (11):

```bash
./llama/llama-bench -m models/smol3/SmolLM3-Q4_K_M.gguf \
  -t 4 -p 128 -n 32 -r 2 -o csv
```

Perpleksnost (12). PPL uspoređuj samo unutar istog modela, na istom tekstu i uz isti `-c`:

```bash
./llama/llama-perplexity -m models/smol3/SmolLM3-Q4_K_M.gguf \
  -f models/tekst/ppl_hr_krat.txt -t 4 -c 512 -b 512
```

KLD prema punom modelu (12):

```bash
./llama/llama-perplexity -m models/smol3/SmolLM3-F16.gguf \
  -f models/tekst/ppl_hr_krat.txt -t 6 -c 512 -b 512 \
  --kl-divergence-base models/smol3/baza-hr.kld
./llama/llama-perplexity -m models/smol3/SmolLM3-Q4_K_M.gguf \
  -f models/tekst/ppl_hr_krat.txt -t 6 -c 512 -b 512 \
  --kl-divergence-base models/smol3/baza-hr.kld --kl-divergence
```

Datoteka `.kld` za kratki tekst iz knjige ima oko 196 MB; ne spremaj je na sinkronizirani disk.

## Formule

```text
veličina   = broj parametara × bajtova po parametru            (7)
bpw        = 8 × bajtova / parametara                         (11)
KV (bajt.) = 2 · c · L · h · d · b / 8                         (8)
memorija  ≈ težine + KV cache + sustav                         (8)
tok/s     ≈ propusnost / veličina modela (gornja granica)      (8)
LoRA       = r × (d + k) parametara, 2 bajta po parametru     (15)
PPL        = exp( -(1/N) · Σ ln P(token i | tokeni prije) )   (12)
```

Oznake u KV: c duljina konteksta, L `num_hidden_layers`, h `num_key_value_heads`, d `head_dim`, b bitova po broju (16 za FP16). Ako nema `num_key_value_heads`, uzmi `num_attention_heads`; ako nema `head_dim`, računaj `hidden_size / num_attention_heads`. Formula je za klizni prozor previsoka, pa vjeruj logu (8).

Provjera računa na Llami 3 8B, Q4_K_M, kontekst 32 768, FP16, uz 5 % rezerve za težine (8, 11):

```text
5,13 GB težine + 4,29 GB KV cache + 1,00 GB sustav = 10,43 GB
```

Za brzu procjenu: datoteka + kontekst + rezerva. Adapter za cijeli 8B uz r = 16 ima oko 84 MB (15).

## Koju razinu izabrati (11)

| Situacija | Kreni od | Napomena |
|---|---|---|
| Ne znaš | Q4_K_M | Razumna početna točka |
| Memorije ima dovoljno | Q8_0 | Najveća i najsporija od ovih razina |
| Između | Q5_K_M, Q6_K | Kad Q4_K_M griješi, a Q8_0 ne stane |
| Q4_K_M ne stane | manji kontekst, pa Q3_K_M | Uz imatrix; razmisli o manjem modelu |
| Ispod Q3 (Q2_K, IQ1, IQ2) | pokus | Očekuj vidljivu štetu |

Šteta ovisi o jeziku, pa odluku potvrdi zlatnim skupom (12).

## Prva pomoć

Puno stablo kvarova je u poglavlju 19. Tri kvara koja se u poglavljima najčešće vraćaju:

::: {.kvar}
**Simptom → uzrok**

- Prazan odgovor ili odgovor bez kraja, `finish_reason: length` → razmišljanje je pojelo proračun tokena. Dodaj `-rea off` ili `--reasoning off`, ili povećaj `max_tokens` (2, 5).
- Model nastavlja tvoje pitanje, ne staje ili ispisuje `<|im_end|>` → predložak se ne primjenjuje ili je pogrešan. Pogledaj `/apply-template` i usporedi niz s izvornim (3, 4, 5).
- Ruši se pri učitavanju ili kad povećaš `-c` → premalo memorije, a KV cache se rezervira odmah. Izračunaj ga i smanji `-c` (2, 8).
:::
