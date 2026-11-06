# Prilozi uz priručnik *Od vozača do mehaničara*

Ovdje su podaci i skripte s kojima su izmjerene brojke u knjizi. Sve je pokrenuto na CPU-u. Mjerni stroj, potpuni izlazi i ono što nije uspjelo opisani su u `mjerenja.md`.

## Sadržaj

- `podaci/train.jsonl`, `podaci/val.jsonl`: 240 i 60 **sintetičkih** zapisnika u obliku poruka (system, user, assistant).
- `podaci/zlatni.jsonl`: zlatni skup od 40 ručno pisanih zapisnika koji ne dijele predloške s treningom.
- `podaci/shema.json`, `podaci/sustav.txt`: JSON shema i sistemska poruka.
- `podaci/kvaka_prirucnik.md`: kratki priručnik za RAG. Odjeljak o jamstvu namjerno sadrži podmetnutu naredbu.
- `vjezbe/`: skripte, po jedna za vježbu (`l1`...`l12`), te pomoćni `mjeri.py` i `posluzitelj.py`. Uz njih `odgovori.py` i `sumnjivi.py` (provjere podataka iz poglavlja 14) te u `podaci/` `sustav2.txt` (sistemska poruka s definicijama hitnosti, poglavlje 13).

Kvaka d.o.o. je izmišljena tvrtka. Skup za trening izrađen je iz 12 predložaka i rječnika (`vjezbe/l7_generiraj.py`, sjeme 42), pa nije zamjena za stvarne zapisnike: model koji ga dobro nauči na zlatnom skupu može biti znatno slabiji.

## Najbrži put: jedna skripta

`pokreni_vjezbe.py` priprema radnu mapu, pokreće sve CPU vježbe i uspoređuje rezultate s brojkama iz knjige. Radi na Windowsu i treba Python 3.14, Git for Windows i oko 40 GB na lokalnom disku. Sve vježbe traju oko 3 sata na mjernom stroju.

```bash
python pokreni_vjezbe.py popis
python pokreni_vjezbe.py priprema C:/vjezbe
python pokreni_vjezbe.py pokreni C:/vjezbe sve
python pokreni_vjezbe.py usporedi C:/vjezbe
```

Umjesto `sve` možeš navesti pojedine vježbe, npr. `L3 L7`. Završene vježbe se preskaču, a `--ponovi` ih pokreće iznova. Naredba `usporedi` piše `izvjestaj.md`. Stroge provjere gledaju što ne bi smjelo ovisiti o stroju (veličine datoteka, perpleksnost, točnost, tokene, sažetke podataka), dok se brzina i memorija samo prikazuju. Točnost i gubitak mogu se malo razlikovati među procesorima, pa odstupanje pregledaj prije nego što zaključiš da je knjiga zastarjela.

Skripta ne pokreće `--samo-velicine` iz `l9_trening.py` ni naknadna mjerenja iz zadnjeg dijela datoteke `mjerenja.md`.

## Inačice

Točan popis je u `okruzenje/`: `verzije.json` (llama.cpp, revizije i kontrolni zbrojevi modela), `requirements.txt` i `requirements-mergekit.txt`. `preuzmi.py` preuzima točno te revizije. Podaci iz `okruzenje/referenca` služe usporedbi.

| Alat | Inačica |
|---|---|
| Windows | 11 Pro 10.0.26300 |
| Python | 3.14.5 |
| torch | 2.15.0+cpu |
| transformers | 5.22.1 |
| peft | 0.21.2 |
| safetensors | 0.8.0 |
| accelerate | 1.15.0 |
| datasets | 5.1.0 |
| huggingface_hub | 2.4.0 |
| llama.cpp | b12110 (`cd959bae9`), `llama-b12110-bin-win-cpu-x64.zip` |
| mergekit | 0.1.5 |

## Priprema

Sve naredbe pokreću se iz radne mape na lokalnom disku, nikad na disku koji se sinkronizira u oblak. Radna mapa mora imati ovakav raspored:

    llama/          raspakirani llama.cpp b12110
    llama-src/      izvorni kod iste oznake, zbog convert_hf_to_gguf.py i gguf-py
    models/         modeli i međurezultati
    podaci/         kopija mape podaci iz ovih priloga
    skripte/        kopija mape vjezbe iz ovih priloga
    okruzenje/      kopija mape okruzenje iz ovih priloga
    logovi/         prazna mapa za ispise
    grafovi/        prazna mapa za CSV datoteke
    venv/           Python okruženje

```bash
py -3.14 -m venv venv
venv/Scripts/python -m pip install -r okruzenje/requirements.txt
venv/Scripts/python -X utf8 skripte/preuzmi.py models qwen gemma smol3 smol2 bge granite
```

Na Windowsu uvijek dodaj `-X utf8`, inače se dijakritici u ispisu pokvare. Za `curl` tijelo zahtjeva šalji iz UTF-8 datoteke (`--data-binary @upit.json`), jer `-d "...č..."` vrati pogrešku 400.

Pretvorba u GGUF mora koristiti `gguf-py` iz iste oznake llama.cpp. Paket `gguf` 0.19.0 s PyPI-ja ruši `convert_hf_to_gguf.py` s `AttributeError: LazyChunkedTensor`.

## Pokretanje po vježbama

| Vježba | Naredba | Trajanje na mjernom stroju |
|---|---|---|
| L1 | `bash skripte/l1_prva_voznja.sh`, `bash skripte/l1_posluzitelj.sh`, `bash skripte/l1_curl.sh` | oko 8 min |
| L2 | `python -X utf8 skripte/l2_mapa_modela.py models/SmolLM3-3B` | sekunde |
| L3 | `python -X utf8 skripte/l3_tokeni.py models/SmolLM3-3B models/SmolLM2-135M-Instruct GEMMA.gguf QWEN.gguf` | 1 min |
| L4 | `python -X utf8 skripte/l4_predlosci.py GEMMA.gguf models/SmolLM3-3B models/SmolLM2-135M-Instruct logovi/l4_server.txt`, zatim `l4b_predlosci.py GEMMA.gguf logovi/l4b_server.txt` | oko 5 min |
| L5 | `python -X utf8 skripte/l5_memorija.py logovi/l5_raw.txt grafovi/memorija_kontekst.csv GEMMA.gguf QWEN.gguf SMOL3.gguf` | 3 min |
| L6 | `l6_tekstovi.py`, pa `convert_hf_to_gguf.py`, pa `l6_kvantizacija.py quant`, `bench`, `ppl`; redoslijed je u `glavni_lanac.sh` | 15 min kvantizacija, oko 3 min po razini za ppl |
| L7 | `python -X utf8 skripte/l7_generiraj.py podaci`, `python -X utf8 skripte/l7_provjeri.py podaci` | sekunde |
| L8 | `python -X utf8 skripte/l8_tocnost.py MODEL.gguf NAZIV podaci LOG CSV --no-rea` | oko 10 min |
| L9 | `python -X utf8 skripte/l9_trening.py models/SmolLM2-135M-Instruct podaci models/l9/glavni --epohe 5 --r 8 --lr 5e-4`, zatim `bash skripte/l9_lanac.sh` | 35 min i 5 min |
| L10 | `python -X utf8 skripte/l10_kirurgija.py models/SmolLM2-135M-Instruct models/l10`, `bash skripte/l10_mergekit.sh`, `bash skripte/l10_mergekit2.sh` | 5 min |
| L11 | `python -X utf8 skripte/l11_opterecenje.py GEMMA.gguf LOG CSV` | oko 15 min |
| L12 | `python -X utf8 skripte/l12_rag.py GEMMA.gguf BGE.gguf GRANITE.gguf podaci/kvaka_prirucnik.md LOG` | oko 10 min |

`GEMMA.gguf` je `models/gemma-4-E2B-it-GGUF/gemma-4-E2B-it-Q4_K_M.gguf`, `QWEN.gguf` je `models/Qwen3-4B-GGUF/Qwen3-4B-Q4_K_M.gguf`, a `SMOL3.gguf` je `models/smol3/SmolLM3-Q4_K_M.gguf`. Za L9 je model `HuggingFaceTB/SmolLM2-135M-Instruct`; oznaka `-v0.2` ne postoji kao javni repozitorij. Skripta `l10_mergekit2.sh` postoji zato što se `immutables` na Pythonu 3.14 bez prevoditelja ne može instalirati: koristi se njegova čista Python inačica.

Trajanja su približna i ovise o tome što još radi na računalu. Brzine su se na istom stroju u istom danu razlikovale i do dva puta.

## Napomene o putanjama i ograničenjima skripti

- Skripte su one iz mjerenja. Naknadno su promijenjene samo `preuzmi.py` i `l10_mergekit*.sh`, da koriste točne inačice; izvornici su u `tools/sirovo/skripte` repozitorija. Putanje su relativne prema radnoj mapi opisanoj gore i tvrdo upisane (`llama/llama-server.exe`, `models/...`, `logovi/...`, `podaci`, `grafovi/...`). Bash skripte (`l1_*.sh`, `l9_lanac.sh`, `glavni_lanac.sh`, `l10_mergekit*.sh`) uz to koriste `venv/Scripts/python`, `taskkill` i `cygpath`, dakle rade samo u Git Bashu na Windowsu. `glavni_lanac.sh` je zapis redoslijeda kojim su izvedene vježbe L9 do L12 i L6 (imatrix, ppl), a ne univerzalna skripta. Neke skripte očekuju datoteke koje ovdje nisu priložene (`models/tekst/*.txt` nastaje pokretanjem `l6_tekstovi.py`; `models/l9/...` nastaje treningom).
- Izvadci s Wikipedije korišteni u mjerenju su u `podaci/tekst` (CC BY-SA, vidi `ATRIBUCIJA.md`), a u radnu mapu idu u `models/tekst`. Modeli se preuzimaju s `preuzmi.py`, a puni članci s `l6_tekstovi.py` (čeka 8 s između zahtjeva).
- `mjeri.py` mjeri memoriju samo kad je izravno pokrenuta naredba stvarni proces. Za Python pokrenut iz `venv\Scripts\python.exe` vraća brojku launchera (5 MB), pa te vrijednosti iz logova treninga ne vrijede.
- Logovi i CSV izmjerenih vrijednosti nisu u ovoj mapi: sažeti su u datoteci `mjerenja.md`, a CSV-ovi u `grafovi/`.
