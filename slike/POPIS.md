# Popis slika (naziv: sadržaj → poglavlje)
- naslovnica.svg: tehnički crtež motora koji se pretvara u matricu brojeva → naslovnica
- karta-knjige.svg: vozi → otvori → mjeri → mijenjaj → isporuči, s poglavljima → 1
- put-tokena.svg: od teksta do odgovora: tekst → predložak → tokenizator → model → logiti → uzorkovanje → token, petlja → 2 ili 5
- mapa-modela.svg: datoteke u mapi modela i čemu služe → 3
- predlozak.svg: poruke (JSON) → Jinja predložak → stvarni tekst s posebnim tokenima → 5
- motor.svg: embedding → N puta (pažnja + MLP) → logiti → 6
- moe.svg: sloj s više stručnjaka i usmjerivačem; ukupni i aktivni parametri → 6
- bitovi.svg: raspored znak/eksponent/mantisa za FP32, BF16, FP16, FP8 E4M3, FP8 E5M2, u mjerilu → 7
- memorija-stog.svg: težine + KV cache + sustav; primjer 5,13 + 4,29 + 1,0 = 10,43 GB, u mjerilu → 8
- prefill-generiranje.svg: dvije faze i što ih ograničava → 8
- kvantizacija-ideja.svg: kako se 16-bitni brojevi zaokružuju na 16 razina u bloku → 11
- odluka.svg: stablo prompt → strukturirani izlaz → RAG → LoRA → 13
- rag.svg: tok RAG-a: dokumenti → komadi → embedding → pretraga → prompt → odgovor → 13
- lora.svg: W0 zamrznut + (α/r)·B×A, veličine matrica u mjerilu → 15
- spajanje.svg: passthrough i TIES/DARE ideja → 17
- looped.svg: Dory: ulazni blok → ponavljajući blok ×N → izlazni blok → 19
- cijeli-put.svg: cjelovit cjevovod → 19
Mjerene grafove crta zadnji korak iz tools/grafovi/*.csv: kvant-velicina.svg → 11, gubitak-krivulje.svg → 16.
