# Kako izabrati model

::: {.cilj}
**Nakon ovog poglavlja znaš:**

- suziti izbor filtrom: licenca, hardver, jezik, zadatak, vlastiti test
- pročitati karticu modela (model card) i licencu te razumjeti što znači ono što u njima nedostaje
- napraviti zlatni skup i njime ocijeniti model polje po polje
- usporediti dva modela na vlastitim podacima
:::

Iz poglavlja 8 znaš koliko memorije model traži. Sada biraš između tisuća modela, a većina vodiča počinje od pogrešnog pitanja: koji je najbolji?

## Pogrešan put: vrh rang-liste

Rang-lista (leaderboard) kaže tko je najbolje riješio tuđi test, a tvog zadatka na njemu nije bilo. Ni same se liste ne slažu: u listopadu 2026. kao najbolji modeli otvorenih težina navođeni su, ovisno o izvoru, Kimi K3, MiMo-V2.6-Pro i DeepSeek V4.1 Flash (sekundarni izvori, poredak namjerno ne navodimo).

Prvo mjesto može biti i neupotrebljivo. Kimi K3 ima 2,8 bilijuna parametara, od čega 104 milijarde aktivnih (sekundarni izvor). Iz poglavlja 6 znaš da kod MoE-a svi stručnjaci ostaju u memoriji, pa takav model neće stati na tvoje računalo. Pobjednik utrke ne pomaže ako ne stane u tvoju garažu.

## Filter koji radi

Idi od najjeftinije provjere prema najskupljoj. Čitanje licence traje minutu, a vlastiti test popodne.

| Korak | Pitanje | Kvaka d.o.o. |
|---|---|---|
| 1. Licenca | Smijem li ga koristiti ovako? | komercijalno, što manje uvjeta |
| 2. Hardver | Stane li i je li dovoljno brz? | laptop, 16 GB, bez GPU-a |
| 3. Jezik | Radi li na hrvatskom? | kartica ne odgovara, ide u test |
| 4. Zadatak | Tekst, kod, slika, alati? | tekst u JSON |
| 5. Test | Kako radi na mojim podacima? | zlatni skup |

Na kraju ostanu dva ili tri kandidata, a ocjenu daje samo korak 5.

## Čitanje kartice modela: Gemma 4 E2B

Karticu modela iz poglavlja 3 piše autor modela, pa je čitaj kao prospekt: činjenice su korisne, a pohvale ne vrijede. Evo kartice `google/gemma-4-E2B-it` (stanje u studenom 2026.), odjeljak po odjeljak.

| Odjeljak | Što piše | Što ti to znači |
|---|---|---|
| Veličina | 2,3 mlrd efektivnih, 5,1 mlrd s embeddingom | "E2B" je manji broj od dva |
| Namjena | chatbotovi, sažimanje, izvlačenje iz slika; popis "nije potpun" | izvlačenje iz teksta nije navedeno, ni zabranjeno |
| Podaci | web, kod, slike, audio, do siječnja 2025., 140+ jezika | ne znaš koliko je hrvatskog |
| Ograničenja | može dati netočne ili zastarjele tvrdnje | općenito, vrijedi za svaki model |
| Evaluacija | MMLU Pro 60,0 %, GPQA Diamond 43,4 % | autorov test, tuđi zadatak |

Najvrjednije su brojke unutar obitelji: isti test daje 60,0 % za E2B i 85,2 % za 31B. Pohvala o "frontier-level" učinku u svakoj veličini to ne spominje. Rezultate o sigurnosti kartica daje samo riječima, bez brojki.

**Što znači ono čega nema.** Kartica ne imenuje hrvatski, nema popisa onih "35+" podržanih jezika i nema testa izvlačenja podataka. To nije ni zabrana ni obećanje: možda je testirano i prešućeno, a možda nikad nije testirano. Razliku ne možeš saznati, pa takve stavke idu na tvoj popis za test.

Za usporedbu, kartica `HuggingFaceTB/SmolLM3-3B` objavljuje skupove podataka za predtrening i konfiguracije treninga, pa o podacima znaš više. Navodi i šest izvorno podržanih jezika, među kojima je njemački, a metapodaci navode osam oznaka, među kojima njemačkog nema. Ni metapodaci nisu konačna riječ. Hrvatskog nema ni na jednom od ta dva mjesta.

## Licence u praksi

::: {.napomena}
Ovo nije pravni savjet. Mjerodavan je tekst licence uz točnu inačicu modela. Ako o tome ovisi posao, pitaj pravnika.
:::

| Licenca | Komercijalno | Kad dijeliš | Izlazi, podešeni model | Primjer |
|---|---|---|---|---|
| Apache 2.0 | da | zadrži licencu i obavijesti, označi izmjene | bez posebnih uvjeta | Gemma 4, Qwen3, SmolLM3 |
| MIT | da | zadrži obavijest o autorskim pravima | bez posebnih uvjeta | DeepSeek V4.1 Flash (sekundarni izvori) |
| OpenMDW-1.1 | da | zadrži ugovor i obavijesti o podrijetlu | izlazi izričito bez obveza | NVIDIA Dory1.0-4B |
| Llama 3.1 Community | da, uz prag 700 mil. korisnika | kopija ugovora, vidljivo "Built with Llama" | ime dijeljenog modela počinje s "Llama" | Llama 3.1 |
| Muse Model License | uz uvjete (sekundarni izvori) | "Built with Muse Spark Open" | izvedeni model nasljeđuje uvjete | Muse Spark Open |
| Istraživačka, nekomercijalna | ne | prema tekstu | prema tekstu | ovisi o modelu |

Prag kod Llame računa se na dan izdanja inačice, a iznad njega tražiš posebnu licencu od Mete. Kod OpenMDW-a prava prestaju ako pokreneš tužbu tvrdeći da materijali modela krše patent ili autorsko pravo, osim ako je to odgovor na tužbu protiv tebe. Te dvije licence pročitane su izravno. Za Muse su uvjeti iz sekundarnih izvora, koji spominju i prag od 20 milijuna USD prihoda za ponudu modela kao usluge, ali ga različito opisuju. Repozitorij traži odobrenje pristupa, pa tekst nije pročitan: provjeri ga. Kimi K3 i GLM-5.3 također imaju posebne uvjete (sekundarni izvori).

Uz svaku licencu postavi tri pitanja:

- Smijem li ga koristiti u tvrtki? Interna upotreba često se već računa kao komercijalna.
- Što moram učiniti kad dijelim podešeni model ili proizvod s njim (ime, navod, kopija licence)?
- Smijem li izlazima modela trenirati drugi model? Kod Llame 3.1 i to povlači pravilo o imenu.

Kvantizirana kopija ne može ti dati više prava od izvornika, pa prati oznaku `base_model`. Oznaka `license:other`, kakvu ima Muse Spark Open, znači da se tekst mora pročitati.

## Benchmarki

Benchmark je standardni ispit s poznatim odgovorima. Prema kartici SmolLM3, AIME mjeri matematička natjecanja, LiveCodeBench programiranje, IFEval praćenje uputa, BFCL pozive alata, a Global MMLU višejezična pitanja. Provjeri tri stvari:

- **Tko je mjerio.** Brojke u kartici samoprijavljene su (self-reported): autor bira testove, postavke i s kim se uspoređuje. Neovisni izvori poput Artificial Analysisa mjere sami, ali i oni imaju vlastite testove.
- **U kojem načinu rada.** Kod SmolLM3 razmišljanje (thinking) podiže AIME 2025 s 9,3 na 36,7, a IFEval spušta sa 76,7 na 71,2.
- **Na kojoj kopiji.** Ove kartice ne kažu da je testirana baš tvoja Q4_K_M, a štetu od kvantizacije mjeriš u poglavlju 12.

Hrvatskog tu nema jer se ispiti grade na engleskom i velikim jezicima. SmolLM3 objavljuje rezultate za osam drugih jezika, a Gemma jedan višejezični zbroj (MMMLU 67,4 %). Pojedini jezik u njemu ne vidiš. Postoji BENCHić (`clarinsi/benchich`), benchmark za bosanski, hrvatski, crnogorski i srpski (stanje u studenom 2026.). Koristan je kao pokazatelj, ali izvlačenje servisnih polja ni on ne mjeri.

## Hrvatski testiraš sam

Hrvatski se u oznakama teško nađe. Kartica Gemme uopće nema oznaku jezika, pa ti je filter `hr` na Hugging Faceu ne bi ni pokazao, a hrvatski ipak razumije. Zato pokreni model na desetak svojih hrvatskih tekstova i pročitaj odgovore. Traži:

- **izmišljene riječi i dijelove:** Qwen3-4B je kod nas napisao "ventilatorno vratilo", a odgovor započeo s "Uživački, stranci,"
- **srpske i druge oblike:** Gemma je u istom pokusu napisala "crevo"
- **tekst bez dijakritika i žargon:** "frizider", "vešmašina", "rerna"
- **jezik razmišljanja:** kod Gemme i Qwena bio je engleski i kad je pitanje hrvatsko, a Qwen je perilicu rublja pročitao kao "Rublja shower"

Hrvatski k tome troši 1,35 do 1,90 puta više tokena (poglavlje 4).

## Razmišljanje i vid traže nešto više

**Modeli koji razmišljaju** prije odgovora troše tokene na skriveni tekst. Na laptopu s i5-10210U, 16 GB i bez GPU-a Gemma je potrošila svih 256 tokena i 38,0 s na razmišljanje, bez ijedne rečenice odgovora. Iz kartice zato očitaj kako se razmišljanje gasi (Gemma uklanjanjem tokena `<|think|>`, SmolLM3 sa `/no_think`, a u llama.cpp `--reasoning off`) i računaj ga u proračun tokena. Točnost u ovom poglavlju mjerena je uz isključeno razmišljanje.

**Modeli koji vide** u GGUF-u dolaze kao dvije datoteke. Glavna nosi jezični model, a `mmproj` (multimodal projector) pretvara sliku ili zvuk u ulaz koji jezični model razumije. Bez nje model radi samo s tekstom. U repozitoriju `unsloth/gemma-4-E2B-it-GGUF` uz Q4_K_M od 3,11 GB stoje `mmproj-F16.gguf` od 0,99 GB i `mmproj-F32.gguf` od 1,90 GB. Pribroji je disku i memoriji. Kvaki, koja radi s tekstom, ne treba.

```bash
llama-server -m gemma-4-E2B-it-Q4_K_M.gguf \
  --mmproj mmproj-F16.gguf --port 8080
```

::: {.neprovjereno}
Autor ovu naredbu nije pokrenuo jer nijedna vježba ne koristi sliku. Oblik je iz dokumentacije llama.cpp (`docs/multimodal.md`). Provjeri inačicu alata.
:::

## Veličine i obitelji

Obitelj nudi više veličina, pa unutar iste licence biraš klasu. Datoteke su Q4_K_M (Gemma iz `unsloth`, stanje u studenom 2026.; Llama iz README-a llama.cpp).

| Parametara | Primjer i datoteka | Gdje ima smisla |
|---|---|---|
| 2–5 mlrd | Qwen3-4B 2,5 GB, E2B 3,11 GB, E4B 4,98 GB | laptop, 8–16 GB, CPU |
| 8–12 mlrd | Llama 3.1 8B 4,9 GB, Gemma 12B 7,12 GB | 16–32 GB ili GPU 12–16 GB |
| 26–31 mlrd | 26B A4B 16,95 GB, 31B 18,32 GB | GPU 24 GB, Apple 32 GB i više |
| oko 70 mlrd | Llama 3.1 70B 43,1 GB | 64 GB i više, Apple ili više GPU-a |
| 400 mlrd i više | Llama 3.1 405B 249,1 GB | poslužitelj |

Stupac s hardverom je orijentir i nije mjeren; mjerena je samo Gemma E2B na navedenom laptopu. Za svog kandidata izračunaj memoriju formulom iz poglavlja 8, uz njezine iznimke. Veličina datoteke ne kaže sve: Qwen ima manju datoteku od Gemme, a trošio je 4,9 GB prema 2,8 GB. Gemma 26B A4B ima 3,8 milijardi aktivnih parametara, pa je po kartici gotovo brza kao model od 4 milijarde, ali u memoriji drži svih 25,2 milijarde.

## Gdje tražiti

Na `huggingface.co/models` kombiniraj filtre za biblioteku (GGUF), licencu, broj parametara i zadatak. Filtri se mogu upisati i u adresu (spoji u jedan redak):

```text
https://huggingface.co/models?library=gguf
  &license=license:apache-2.0
  &num_parameters=min:0,max:6B&sort=trending
```

GGUF često ne izrađuje autor modela. Aktivni izdavači kvantiziranih kopija u studenom 2026. su `unsloth`, `bartowski`, `ggml-org` i `lmstudio-community`, a neki autori objavljuju i vlastite (`Qwen/Qwen3-4B-GGUF`). Poznato ime ne zamjenjuje provjeru iz poglavlja 10. Prije preuzimanja pogledaj `base_model`, licencu i datum.

## Zlatni skup

Zlatni skup (gold set) je mali popis stvarnih ulaza s točnim odgovorima, koje je označio čovjek i koje model nikad ne vidi pri treningu. To je tvoj vlastiti ispit, na tvom zadatku i jeziku. Kvakin je u `prilozi/podaci/zlatni.jsonl`:

```json
{"id":5,
 "tekst":"Mikrovalka vrti tanjur i svijetli, ali juha ostane
   hladna. Visoki napon ima, magnetron crko. Nije nikakva žurba,
   ima i običan štednjak.",
 "ocekivano":{"uredaj":"mikrovalna pećnica","kvar":"ne grije",
   "dio":"magnetron","hitnost":"niska"}}
```

Ovdje je zapis prelomljen, a u datoteci je jedan redak.

### Zašto je 40 dovoljno za početak

Četrdeset zapisnika s četiri polja daje 160 ocjena. Jedno polje vrijedi 0,625 boda, a jedan cijeli zapisnik 2,5 boda. Skup je dovoljno velik da uočiš veliku razliku između modela i vidiš vrste grešaka, a dovoljno malen da ga označiš ručno i pokrećeš nakon svake promjene. Razlika od nekoliko polja može biti slučajna, pa za gotovo jednake kandidate skup treba povećati.

### Kako ga napraviti

1. **Uzmi stvarne slučajeve.** Kvaka je izmišljena, pa su njezini zapisi pisani ručno. Ti uzmi prave zapisnike i ukloni osobne podatke.
2. **Ne uzimaj ih iz podataka za trening.** Inače mjeriš pamćenje. Kvakin skup namjerno je drukčiji: s treningom dijeli 0,5 % trigrama riječi, a zapisnici imaju prosječno 28,0 riječi prema 15,3. Mali podešeni model u poglavlju 16 zato daje 81,7 % na validaciji, a samo 43,8 % na zlatnom skupu.
3. **Uključi teške primjere.** "Ledenica" je zamrzivač (id 17), "guma" na stroju za suđe je brtva (id 1), a kad nitko nije otvorio uređaj, točan dio je `nepoznato` (id 38).
4. **Pokrij sve vrijednosti.** U Kvakinu skupu svaka vrijednost polja pojavljuje se barem jednom, a hitnost je podjednako raspoređena (15, 13, 12).
5. **Odvoji ga zauvijek.** Nikad ne ide u trening, a primjere iz njega ne prepisuj u prompt.

### Pravilo ocjenjivanja po polju

Pravilo zapiši prije prvog pokretanja, da ga kasnije ne prilagođavaš rezultatu. Kvakino je strogo: nakon uklanjanja rubnih razmaka i svođenja na mala slova vrijednost mora biti jednaka očekivanoj. Polje koje nedostaje je pogrešno, a "cijeli zapisnik" znači sva četiri polja točna. Za polja poput datuma ili imena moraš odrediti svoj način usporedbe.

```python
polja = ["uredaj", "kvar", "dio", "hitnost"]
ocekivano = {"uredaj": "mikrovalna pećnica", "kvar": "ne grije",
             "dio": "magnetron", "hitnost": "niska"}
dobiveno = {"uredaj": "mikrovalna pećnica", "kvar": "magnetron",
            "dio": "magnetron", "hitnost": "srednja"}

def norm(v):
    return str(v).strip().lower()

tocna = [p for p in polja
         if norm(dobiveno.get(p, "")) == norm(ocekivano[p])]
print(f"{len(tocna)}/4", tocna)
```

```text
2/4 ['uredaj', 'dio']
```

Skripta `prilozi/vjezbe/l8_tocnost.py` radi to za cijeli skup. Pokreće `llama-server`, šalje svaki zapisnik s `temperature 0` i ispisuje točnost po polju, cijele zapisnike i latenciju, u dva načina: `shema` (JSON shema u zahtjevu, detalji u poglavlju 13) i `prompt` (ista sistemska poruka, bez sheme).

### Stvarni rezultat: Gemma sa shemom i bez nje

Gemma 4 E2B Q4_K_M, laptop i5-10210U, 16 GB, bez GPU-a, 4 dretve, razmišljanje isključeno:

| Način | Valjan JSON | Točnost po polju | Cijeli zapisnik | p95 |
|---|---|---|---|---|
| shema | 40/40 | 74,4 % | 12/40 | 6,7 s |
| prompt | 40/40 | 71,25 % | 11/40 | 7,9 s |

Po poljima (shema / prompt): uređaj 36/36, kvar 27/23, dio 30/29, hitnost 26/26 od 40.

Bez sheme, id 1. Odgovor je "valjan JSON", a guma se ne nalazi među dopuštenim dijelovima:

````text
```json
{
  "uredaj": "perilica posuđa",
  "kvar": "curi voda",
  "dio": "guma",
  "hitnost": "visoka"
}
```
````

Bez sheme, id 5. Dio je upisan u polje za kvar, pa je mikrovalnoj kvar "magnetron":

````text
```json
{
  "uredaj": "mikrovalna pećnica",
  "kvar": "magnetron",
  "dio": "magnetron",
  "hitnost": "srednja"
}
```
````

Sa shemom se takvi odgovori ne mogu pojaviti, ali pogrešan odgovor ostaje. Za id 1 model tada kaže `"dio": "grijač"`: oblik je besprijekoran i vrijednost dopuštena, a sadržaj pogrešan. Takvu grešku ne može uhvatiti nikakva provjera oblika, samo usporedba s točnim odgovorom.

Bez sheme je 12 vrijednosti izvan dopuštenih, a svih 40 odgovora umotano je u oznaku koda, koju skripta preskoči kad traži `{...}`. Sa shemom izvan dopuštenih nema nijedne. U oba načina ima 14 grešaka u hitnosti i sve idu u istom smjeru, stupanj više (12 puta `niska` kao `srednja`, 2 puta `srednja` kao `visoka`). Sistemska poruka nabraja hitnosti, ali ne kaže što koja znači. To ipak nije cijeli uzrok: poruka s definicijama, koju mjeri poglavlje 13, dala je opet 26/40.

**Pouka: "valjan JSON" ne znači točan.** Brojač je pokazao 40/40 u oba načina, a točna su bila otprilike tri polja od četiri. Shema jamči oblik. Dobitak od 5 polja od 160, oko 3 boda, premalen je da bi se tumačio kao stvarna razlika.

**Prema cilju.** Kvaka traži točnost po polju od barem 90 %, odnosno 144 polja od 160. Gemma ih ima 119, dakle 25 premalo. Ni p95 od 6,7 s ne ispunjava cilj od 5 s na ovom laptopu. Bez zlatnog skupa model bi izgledao gotov jer je svaki odgovor JSON. Sada znaš gdje griješi, a poglavlje 13 odlučuje što s tim.

Isti skup, skripta i pravilo ostaju do kraja knjige: pokrećeš ih nakon svake promjene, primjerice kvantizacije u poglavlju 12 i treninga u poglavlju 16.

## Usporedba dvaju modela

Tri pitanja iz poglavlja 2 nisu bila usporedba. Ozbiljna izgleda ovako:

| Stavka | Gemma 4 E2B Q4_K_M | Drugi model | Cilj |
|---|---|---|---|
| Licenca | Apache 2.0 | | po filtru |
| Datoteka | 3,11 GB | | |
| Vršna memorija | 2756 MiB | | stane |
| Točnost po polju, shema | 74,4 % | | ≥ 90 % |
| Cijeli zapisnik | 12/40 | | |
| Najslabije polje | hitnost 26/40 | | |
| p95 latencija | 6,7 s | | ≤ 5 s |
| Stroj, inačica alata | i5-10210U, b12110 | | isti |

Uvjeti moraju biti jednaki: isti stroj, ista sistemska poruka, isti `max_tokens`, razmišljanje u istom stanju. Brzine su se na mjernom laptopu istog dana razlikovale i do dva puta, pa male razlike u latenciji ne tumači kao stvarne.

::: {.vjezba}
**Vježba: ocijeni model zlatnim skupom** `CPU` · RAM 4 GB · disk 3,2 GB · 10 min

Pripremi radnu mapu kako piše u `prilozi/README.md`: `llama/`, `models/`, `podaci/`, `skripte/`, prazne `logovi/` i `grafovi/`. Skripta treba samo standardni Python, ali je pisana za Windows (`llama-server.exe`, `WinDLL` u `mjeri.py`). Na Linuxu i macOS-u moraš prepraviti `posluzitelj.py` i `mjeri.py`. Putanju modela prilagodi svojoj.

```bash
python -X utf8 skripte/l8_tocnost.py \
  models/gemma-4-E2B-it-GGUF/gemma-4-E2B-it-Q4_K_M.gguf \
  Gemma-4-E2B-Q4_K_M podaci logovi/l8_server.txt \
  grafovi/tocnost_zlatni.csv --no-rea
```

Izlaz na mjernom laptopu (prelomljen po širini stranice):

```text
== Gemma-4-E2B-Q4_K_M / shema: n=40 valjan JSON 40/40
   tocnost po polju 74.4 %  cijeli zapisnik 12/40
   po polju: {'uredaj': '36/40', 'kvar': '27/40',
              'dio': '30/40', 'hitnost': '26/40'}
   latencija p50 5.9 s, p95 6.7 s, ukupno 235 s,
   generiranje medijan 10.1 tok/s, peak WS 2756 MB
```

Skripta piše MB, a to su zapravo MiB (poglavlje 8). Tvoje latencije i memorija bit će drukčije, a mogu se razlikovati i odgovori, pa izmjeri svoje. Zatim:

1. Otvori `logovi/l8_server.txt.Gemma-4-E2B-Q4_K_M.prompt.json` i nađi odgovor za id 1. Je li i kod tebe `guma`?
2. Pokreni drugi model istom naredbom, uz drugi naziv.
3. Popuni tablicu usporedbe i napiši koji model biraš za Kvaku i zašto.

```bash
python -X utf8 skripte/l8_tocnost.py \
  models/Qwen3-4B-GGUF/Qwen3-4B-Q4_K_M.gguf \
  Qwen3-4B-Q4_K_M podaci logovi/l8_qwen.txt \
  grafovi/tocnost_zlatni.csv --no-rea
```

Naše pokretanje Qwena istom naredbom, uz napomenu da je na istom laptopu tada radio i drugi pokus, pa su latencije i brzine nepouzdane (ispis skraćen na tri retka po načinu):

```text
== Qwen3-4B / shema: n=40 valjan JSON 40/40
   tocnost po polju 66.2 %  cijeli zapisnik 4/40
   po polju: {'uredaj': '34/40', 'kvar': '24/40',
              'dio': '29/40', 'hitnost': '19/40'}
== Qwen3-4B / prompt: n=40 valjan JSON 40/40
   tocnost po polju 66.2 %  cijeli zapisnik 4/40
   po polju: {'uredaj': '34/40', 'kvar': '22/40',
              'dio': '31/40', 'hitnost': '19/40'}
```

Oba načina daju 106 od 160 polja, a Gemma sa shemom 119. Kod Qwena je razlika između sheme i prompta nula polja, pa se nikakva prednost sheme ne vidi. Vršna memorija bila je 4077 MiB, p50 latencija 14,1 s i p95 19,4 s (sa shemom), generiranje oko 4,5 tokena u sekundi. Drugi stupac tablice zato glasi: Apache 2.0, 2,50 GB, 4077 MiB, 66,2 %, 4/40, hitnost 19/40, p95 19,4 s (uz opterećenje). Na zlatnom skupu Gemma je dakle ispred, a latenciju ne uspoređuj dok se ne izmjeri bez drugog posla na stroju.
:::

::: {.kvar}
**Simptom → uzrok**

- Valjan JSON 40/40, a niska točnost → ispravan oblik, pogrešno značenje. Gledaj točnost po polju i pročitaj odgovore.
- Vrijednost izvan popisa (`"dio": "guma"`) → nema sheme. Dodaj `response_format` s JSON shemom (poglavlje 13).
- Sjajno na validaciji, slabo na zlatnom skupu → model je naučio tvoje predloške. Vjeruj zlatnom skupu (poglavlje 16).
- Jedno polje griješi uvijek u istom smjeru → pravilo možda nije definirano u promptu. Provjeri poruku i svoje oznake.
- Prazan `content` ili prekinut JSON → razmišljanje je pojelo proračun. Dodaj `--reasoning off` ili povećaj `max_tokens`.
- Kartica hvali višejezičnost, a hrvatski je loš → prosjek ne govori o tvom jeziku. Testiraj vlastitim tekstovima.
- Greška da model ne prima sliku → nedostaje `mmproj`. Preuzmi je iz istog repozitorija.
:::

## Sažetak

Model biraš filtrom od najjeftinije provjere prema najskupljoj: licenca, hardver, jezik, zadatak i vlastiti test, a rang-liste i kartice daju samo polazne kandidate. Ono čega u kartici nema, poput hrvatskog, stavljaš na popis za test, a licencu provjeravaš u njezinu tekstu. Zlatni skup od 40 stvarnih, ručno označenih primjera koji nikad ne ulaze u trening ocjenjuje model polje po polje. Gemma 4 E2B na njemu postiže 74,4 % sa shemom i 71,25 % bez nje, uz 40/40 valjanih JSON-a i odgovore poput `"dio": "guma"`, što je ispod Kvakinih 90 %. Isti skup ponovno koristiš nakon svake promjene, prvi put već u poglavlju 12.
