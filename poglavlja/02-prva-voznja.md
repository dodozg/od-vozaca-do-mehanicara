# Prva vožnja

::: {.cilj}
**Nakon ovog poglavlja znaš:**

- pokrenuti model na svom računalu i dobiti odgovor na hrvatskom
- pročitati izvještaj o brzini
- pozvati model istim API-jem koji koriste tvoji alati
- prepoznati najčešće kvarove prve vožnje
:::

Za 20 minuta model će ti odgovoriti s tvog računala, bez računa, ključa i slanja podataka u oblak. Ne biraš ništa: model, alat i naredbe zadani su. Razloge saznaješ kasnije, kao što se i voziti uči prije nego što se otvori hauba.

Sve brojke u poglavlju izmjerene su na jednom običnom laptopu: Intel i5-10210U, 16 GB RAM-a, bez grafičke kartice, Windows 11, llama.cpp b12110. Tvoje će biti drukčije, pa ih na kraju izmjeri sam.

::: {.napomena}
**Četiri riječi koje ćeš razumjeti kasnije**

- **GGUF:** format datoteke u kojoj je cijeli model (poglavlje 10).
- **Q4_K_M:** oznaka sažimanja brojeva u modelu, zbog kojeg stane u običan RAM (poglavlje 11).
- **Kontekst:** koliko teksta model drži u glavi tijekom jednog razgovora (poglavlje 8).
- **Temperatura:** koliko se model smije slučajno udaljiti od najvjerojatnije riječi (poglavlje 6).
:::

## Troja vrata

Do lokalnog modela vode troja vrata, a iza njih je često isti motor. Na računalima s NVIDIA ili AMD karticom i LM Studio i Ollama oslanjaju se na llama.cpp ili njegovu biblioteku ggml.

- **LM Studio** je program s prozorima: tražilica modela, razgovor, gumbi. Na Apple Siliconu ima i MLX, drugi motor.
- **Ollama** je jednostavna usluga koja stalno radi u pozadini i sama upravlja modelima.
- **llama.cpp** je motor ispod njih. Ova ga knjiga koristi jer pokazuje svaku postavku, brzinu i upozorenje.

Zato sada ulazimo na treća vrata.

## Priprema

Zadani je model **Gemma 4 E2B** u inačici Q4_K_M, licenca Apache 2.0, datoteka od 3,11 GB, bez prijave i bez čekanja na odobrenje. Izabran je prema mjerenjima s kraja poglavlja, za ovu svrhu i na ovom stroju.

Radna mapa mora biti na lokalnom disku. Google Drive, OneDrive i Dropbox nisu za modele (poglavlje 10).

::: {.vjezba}
**Vježba: preuzimanje** `CPU` · RAM 8 GB · disk 4 GB · 5 do 10 min

Otvori terminal. Na Windowsu je to PowerShell (tipka Windows, upiši `powershell`). Zalijepi ove retke:

```text
mkdir C:\llm\models
cd C:\llm
$u = "https://github.com/ggml-org/llama.cpp/releases/download/b12110/"
curl.exe -L -o llama.zip ($u + "llama-b12110-bin-win-cpu-x64.zip")
Expand-Archive llama.zip -DestinationPath llama
$m = "https://huggingface.co/unsloth/gemma-4-E2B-it-GGUF/resolve/main/"
curl.exe -L -o models/gemma-4-E2B-it-Q4_K_M.gguf `
  ($m + "gemma-4-E2B-it-Q4_K_M.gguf")
```

Na Linuxu otvori Terminal i zalijepi ovo. Na Macu s Apple čipom umjesto `ubuntu-x64` piši `macos-arm64`, a na starijem Macu s Intelom `macos-x64`.

```bash
mkdir -p ~/llm/models && cd ~/llm
U=https://github.com/ggml-org/llama.cpp/releases/download/b12110
curl -L -o llama.tar.gz $U/llama-b12110-bin-ubuntu-x64.tar.gz
tar -xzf llama.tar.gz && mv llama-b12110 llama
M=https://huggingface.co/unsloth/gemma-4-E2B-it-GGUF/resolve/main
curl -L -o models/gemma-4-E2B-it-Q4_K_M.gguf \
  $M/gemma-4-E2B-it-Q4_K_M.gguf
```

Model mora imati točno 3 106 738 272 bajta. Provjeri to naredbom `ls models` u PowerShellu ili `ls -l models` na Linuxu i Macu.
:::

::: {.drugacije}
Autor je model preuzeo skriptom `prilozi/vjezbe/preuzmi.py` (47 s na njegovoj vezi), a llama.cpp iz istog Windows paketa, pa ove naredbe nije izvodio doslovno. Provjerio je da poveznice rade, da model počinje oznakom `GGUF` i da mu je veličina točna te da paketi za Linux i Mac sadrže `llama-cli` i `llama-server`. Na Linuxu i Macu ništa nije pokrenuo jer je mjerni stroj na Windowsu.
:::

Na vezi od 100 Mbit/s model se preuzima oko četiri minute (izračun). Paket za procesor radi i ako imaš grafičku karticu, samo je ne koristi. Pakete za GPU, kao i Appleove čipove, obrađuje poglavlje 8.

## Prvi odgovor, koji nije stigao

Prije naredbe koja radi pogledaj što se dogodilo bez nje. Ovo ne moraš ponavljati. Prvi stvarni pokušaj išao je sa zadanim postavkama: pitanje o perilici, proračun od 256 tokena. Token je komadić teksta, obično nekoliko slova (poglavlje 4). Model je radio 38,0 s, a zatim je ispisao ovo (prelomljeno radi širine stranice):

```text
> Objasni u tri rečenice zašto perilica rublja ne izbacuje vodu i što
  prvo treba provjeriti.

[Start thinking]

Thinking Process:

1.  **Analyze the Request:** The user wants an explanation (in three
sentences) of why a washing machine (perilica rublja) is not draining
water, [...]

5.  **Refine and Translate to Croatian (Focusing on clarity

[ Prompt: 87.8 t/s | Generation: 8.2 t/s ]
```

Tu je kraj. Nijedna rečenica odgovora. Model ima predložak koji mu dopušta da prije odgovora razmišlja u zasebnom bloku, i to na engleskom, iako je pitanje na hrvatskom. Razmišljanje (thinking) troši iste tokene kao i odgovor, pa je svih 256 otišlo na plan odgovora, a ispis je stao usred rečenice. Nikakve greške nije bilo. Program je uredno završio.

Veći proračun dao mu je više prostora: u poglavlju 5 isto je pitanje s granicom od 500 tokena završilo odgovorom, ukupno 368 tokena. Za kratke zadatke razmišljanje isključi. To je jedina razlika između "radi" i "ne radi", a kako to izgleda iznutra, pokazuje poglavlje 5.

## Prvi pravi odgovor

::: {.vjezba}
**Vježba: prvi odgovor** `CPU` · RAM 8 GB · disk 4 GB · 1 min

Iz mape `llm` na Linuxu ili Macu pokreni:

```bash
./llama/llama-cli -m models/gemma-4-E2B-it-Q4_K_M.gguf \
  -st -n 256 -c 4096 -t 4 --perf --seed 1 -rea off \
  -p "Objasni u tri rečenice zašto perilica rublja ne izbacuje vodu \
i što prvo treba provjeriti."
```

U PowerShellu:

```text
$q = "Objasni u tri rečenice zašto perilica rublja ne izbacuje vodu " +
  "i što prvo treba provjeriti."
./llama/llama-cli -m models/gemma-4-E2B-it-Q4_K_M.gguf `
  -st -n 256 -c 4096 -t 4 --perf --seed 1 -rea off -p $q
```
:::

::: {.drugacije}
Autor je iste argumente izvodio iz Git Basha na Windowsu, preko mjerne skripte i s drugom putanjom do modela. U PowerShellu, Linuxu i Macu ova naredba nije pokretana. Ako ti u retku iza `>` dijakritici nisu ispravni, ljuska je pokvarila pitanje: spremi ga u UTF-8 datoteku i umjesto `-p $q` zadaj `-f pitanje.txt`.
:::

Što znače oznake:

- `-m` je datoteka modela, a `-p` pitanje.
- `-rea off` isključuje razmišljanje.
- `-st` znači jedno pitanje i izlaz. Bez njega ostaješ u razgovoru.
- `-n 256` je proračun tokena za odgovor, a `-c 4096` duljina konteksta.
- `-t 4` je broj dretvi procesora, a `--perf` traži izvještaj o brzini.
- `--seed 1` učvršćuje slučajnost (poglavlje 6).

Nakon 24,9 s, s učitavanjem, stiže ovo:

> Perilica rublja ne izbacuje vodu jer je moguće da je instalacija za odvod za vodu začepljena ili da je mrežica za odvod za vodu začepljena. Prvo treba provjeriti da li je spojni otvor za odvod čist i da nema prepreka u cijeloj cijevi. Ako to nije slučaj, trebate provjeriti da li je ventil za odvod otvoren i da li je mrežica za odvod pravilno postavljena.

Upravo ti je odgovorio model koji radi na tvom računalu. Mrežni kabel možeš izvući i ponoviti naredbu.

Pročitaj odgovor kritički. Tri su rečenice tu, smjer je razuman, ali "instalacija za odvod" i "spojni otvor" ne zvuče kao serviser. Svejedno je napisan sigurnim tonom.

### Izvještaj o brzini

Ispod odgovora stoji ovaj redak:

```text
[ Prompt: 88.1 t/s | Generation: 8.3 t/s ]
```

Prvi broj je **prefill**, brzina kojom model čita tvoje pitanje, a drugi je **generiranje**, brzina kojom piše odgovor. Ovdje se razlikuju desetak puta jer se čitanje može raditi usporedno, a pisati se mora token po token. Za osjećaj pri radu važniji je drugi broj. Detalji su u poglavlju 8.

Vršna memorija (RSS) bila je 2,78 GB. U nju su uračunate i težine koje sustav samo mapira s diska, a što to znači, objašnjava poglavlje 8. Na računalu je prije pokretanja bilo slobodno oko 3,5 GB. Oznaka "RAM 8 GB" zato je oprezna preporuka, a na takvom stroju autor nije mjerio.

## Isti model kao usluga

Naredba iz terminala dobra je za probu, ali tvoji alati ne razgovaraju s terminalom. Za njih postoji `llama-server`: drži model učitan i prima zahtjeve preko mreže, u ovom slučaju samo s tvog računala.

```bash
./llama/llama-server -m models/gemma-4-E2B-it-Q4_K_M.gguf \
  -c 4096 -t 4 --port 8080 --host 127.0.0.1 --reasoning off
```

U PowerShellu svaki `\` na kraju retka zamijeni znakom `` ` ``. Model je bio spreman za 8,9 s pri prvom pokretanju, a pri drugom za 3,4 s jer je datoteka već bila u priručnoj memoriji sustava. Kad u ispisu vidiš `listening on http://127.0.0.1:8080`, ostavi taj prozor otvoren i prijeđi u drugi.

U ispisu se pojavljuje i ovo upozorenje: `security: no API key is set and CORS allows all origins`. Poslužitelj ne traži ključ i pušta zahtjeve s bilo koje web stranice. Dok je `--host 127.0.0.1`, s drugih računala ne može mu se pristupiti. Ne otvaraj ga prema mreži bez ključa (`--api-key`) i ugasi ga kad završiš (Ctrl+C).

### Razgovor u pregledniku

Otvori `http://127.0.0.1:8080` i dobivaš prozor za razgovor sličan onima koje već koristiš, s ovim modelom iza njega.

::: {.neprovjereno}
Autor sučelje u pregledniku nije otvarao jer su mjerenja išla kroz `curl`. Da ga poslužitelj zadano nudi na istoj adresi, piše u dokumentaciji `llama-server` (stanje u studenom 2026.).
:::

### Isti API koji već govore tvoji alati

Napravi datoteku `upit.json` u mapi `llm`. U Windowsu je najlakše Notepad, kodiranje UTF-8. Ovdje je sadržaj prelomljen radi širine stranice, a u datoteci sve mora stajati u jednom retku:

```json
{"model":"gemma","seed":1,"max_tokens":128,"messages":[{"role":"user",
"content":"Objasni u tri rečenice zašto perilica rublja ne izbacuje vodu i
što prvo treba provjeriti."}]}
```

Zatim u drugom prozoru pošalji zahtjev. U PowerShellu piši `curl.exe`, a `\` zamijeni znakom `` ` ``.

```bash
curl -s http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" --data-binary "@upit.json"
```

Stvarni odgovor, skraćen na mjestima s `[...]`:

```text
{"choices":[{"finish_reason":"stop","index":0,"message":
{"role":"assistant","content":"Perilica rublja ne izbacuje vodu jer je
moguće da je [...] pravilno postavljena."}}],[...]
"usage":{"completion_tokens":107,"prompt_tokens":36,"total_tokens":143,
[...]"timings":{[...]"predicted_per_second":11.086357390066478}}
```

::: {.drugacije}
Autor je poslužitelj i `curl` pokretao iz Git Basha na Windowsu. Inačice za PowerShell, Linux i Mac nije pokretao, a datoteka `upit.json` kod njega je napravljena skriptom `l1_curl.sh`.
:::

Tekst je od riječi do riječi jednak onom iz terminala. Važan je oblik: `choices`, `message`, `usage`. To je format OpenAI API-ja, koji razumiju mnogi alati. Tako je tijekom mjerenja izgledao prvi uspješan poziv. Prva dva nisu uspjela jer je `curl -d "...č..."` iz ljuske pokvario dijakritike, a poslužitelj je vratio pogrešku 400 (`ill-formed UTF-8 byte`). Zato tijelo ide iz datoteke.

Isti upit poslan još jednom vratio je drukčiji tekst, s izrazima "probolja za odvod" i "crevo", iako je `seed` bio isti. Poslužitelj je tada ponovno iskoristio 31 od 36 tokena pitanja (`cached_tokens`). Autor nije utvrdio je li to razlog. Pouka vrijedi i bez toga: ne računaj da isti zahtjev uvijek daje isti odgovor.

### Spajanje postojeće aplikacije

U aplikaciji koja podržava OpenAI API traži polje koje se obično zove Base URL ili API endpoint, pa promijeni tri vrijednosti:

- adresa: `http://127.0.0.1:8080/v1`
- ključ: bilo kakav tekst, ako ga aplikacija traži (poslužitelj ga ovdje ne provjerava)
- model: bilo koji naziv (poslužitelj je kod nas prihvatio `gemma`, a u odgovoru vratio putanju datoteke)

U Pythonu s bibliotekom `openai` to izgleda ovako:

```python
from openai import OpenAI

klijent = OpenAI(base_url="http://127.0.0.1:8080/v1",
                 api_key="nije-potreban")
odgovor = klijent.chat.completions.create(
    model="gemma",
    messages=[{"role": "user", "content": "Reci dobar dan."}],
)
print(odgovor.choices[0].message.content)
```

::: {.neprovjereno}
Autor ovaj isječak nije pokrenuo jer su mjerenja išla kroz `curl`. Oblik poziva je prema dokumentaciji `llama-server`.
:::

Isti API ne znači iste mogućnosti. Ovaj model pokrenut je kao čisto tekstualni (u ispisu `modalities : text`), a aplikacija koja očekuje slike ili pozive alata može zapeti. API i strukturirani izlaz obrađuje poglavlje 13.

## Ako već imaš LM Studio ili Ollamu

Možeš ih i dalje koristiti za razgovor. Za vježbe u knjizi ostani na llama.cpp jer naredbe i ispisi vrijede samo za njega. Ovo piše u njihovoj dokumentaciji (stanje u studenom 2026.):

- **Ollama:** API je na `http://localhost:11434/v1/`. Razmišljanje se u njezinu vlastitom API-ju isključuje poljem `"think": false`. Oznaka `gemma4:e2b` ne mora biti ista datoteka kao naša.
- **LM Studio:** model se traži u programu, a lokalni poslužitelj sluša na `http://localhost:1234/v1`.

```bash
ollama run gemma4:e2b
```

::: {.neprovjereno}
Autor ni Ollamu ni LM Studio nije pokrenuo, pa za njih nema brzine ni ispisa. Ako model u njima šuti ili dugo razmišlja, provjeri je li razmišljanje uključeno.
:::

## Pošteno: lokalno prema oblaku

Ova knjiga nema izmjerene brojke za modele u oblaku. Zato zalijepi isto pitanje o perilici u alat koji svakodnevno koristiš i usporedi.

- **Brzina.** Ovdje je to između 5,6 i 12,1 tokena u sekundi, a za oblak brojke nemamo. Cijeli poziv kroz poslužitelj trajao je 10,5 s za 107 tokena. Kvakin je cilj latencija p95 do 5 s. Ovo nije test tog cilja, ali je prvi znak da bi taj laptop mogao biti pretijesan.
- **Hrvatski.** Ima grešaka. U drugom pitanju, kratkoj poruci stranci, Gemma je ponudila tri opcije umjesto jedne i prekinula se na 256. tokenu. U trećem, sažetku o neispravnom kompresoru hladnjaka, napisala je netočno "problem u hladnjaku u kompresoru".
- **Ograničenja.** Model radi samo s onim što mu daš: nema pretrage weba ni tvojih datoteka, a proračun i kontekst koje smo ovdje zadali skromni su.
- **Što dobivaš.** Podaci ne napuštaju računalo, radi bez mreže, nema naplate po tokenu i svaka je postavka tvoja. Kada se to isplati, govori tablica iz poglavlja 1.

Ne očekuj da će se mali besplatni model mjeriti s velikim modelom u oblaku. Svrha je prve vožnje da motor proradi kod tebe.

### Zašto baš Gemma: Qwen3-4B

Drugi kandidat bio je `Qwen3-4B-Q4_K_M.gguf` iz repozitorija `Qwen/Qwen3-4B-GGUF`. Datoteka mu je manja, ali na istom stroju, bez razmišljanja:

| | Gemma 4 E2B | Qwen3-4B |
|---|---:|---:|
| Datoteka | 3,11 GB | 2,5 GB |
| Vršna memorija | 2,78 GB | 4,95 GB |
| Prefill, tok/s | 71,2 do 88,1 | 16,6 do 19,6 |
| Generiranje, tok/s | 8,3 do 9,0 | 5,9 do 6,3 |

Manja datoteka trošila je gotovo dvostruko više memorije, što će objasniti poglavlje 8. Na pitanje o perilici Qwen je izmislio dijelove:

> Perilica rublja ne izbacuje vodu moguće zbog zastanka vodnog koluta, oštećenog ventilatora ili zatvorenog ventilatornog vratila. Prvo treba provjeriti da li je pravilno povezana voda i da li ima pritisak. Zatim provjeriti funkcionalnost ventilatora i da li je pravilno otvoren vratilo.

Njegovo razmišljanje, kad je bilo uključeno, pitanje je čitalo kao "Rublja shower". Ipak, sažetak o kompresoru Qwen je napisao točno, a Gemma nije. Tri pitanja s jednim `seed`om nisu statistika. Ozbiljnu usporedbu modela učiš u poglavlju 9.

## Izmjeri svoje

Koliko je brz ovaj model? Ne postoji jedan odgovor. Isti model, isti stroj, isti dan, četiri dretve:

| Alat | Generiranje, tok/s |
|---|---:|
| `llama-completion` | 5,61 |
| `llama-cli` | 8,2 do 9,0 |
| `llama-server` | 11,09 |
| `llama-bench` | 12,06 ± 0,74 |

Raspon je od 5,6 do 12,1. Ne zaključuj iz toga da je poslužitelj brži od `llama-cli`: stroj nije bio izoliran, pokusi su se vrtjeli u lancu, a o zagrijavanju procesora nema podataka. Zaključak je skromniji: tuđa brojka bez alata i stroja malo znači, a ni tvoja jedna brojka ne znači mnogo. Pokreni vježbu tri puta, zapiši oba broja i računaj s rasponom. Skripte za iste pokuse nalaze se u `prilozi/vjezbe/` (`l1_*.sh`, rade u Git Bashu na Windowsu).

Što se točno događa između tvog pitanja i odgovora, korak po korak, crta poglavlje 5.

::: {.kvar}
**Simptom → uzrok**

- Program se ruši pri učitavanju ili javlja da nema memorije → premalo slobodnog RAM-a. Ovdje je model trebao 2,78 GB. Zatvori preglednik i ostale velike programe.
- Vrlo sporo, brzina daleko ispod očekivane → zauzeti procesor, model na sinkroniziranom disku ili prvo čitanje s diska. Ponovi, pa provjeri mapu (poglavlje 10).
- Prazan odgovor ili beskrajno razmišljanje → uključeno razmišljanje pojelo je proračun. Dodaj `-rea off` odnosno `--reasoning off`. Ako je razmišljanje isključeno, a odgovor i dalje prazan, kriv je predložak (poglavlje 5).
- Odgovor stane usred rečenice → model je došao do granice `-n` ili `max_tokens`. Povećaj je.
- Besmislica ili model samo nastavlja tvoj tekst → predložak se ne primjenjuje. Tako se ponašao Qwen u `llama-completion`, koji predložak nije koristio. Provjeri i veličinu datoteke, jer preuzimanje može biti prekinuto (poglavlje 10).
- Pogreška 400 `ill-formed UTF-8 byte` → ljuska je pokvarila dijakritike. Tijelo šalji iz UTF-8 datoteke s `--data-binary`.
- `W load: control-looking token: 1 '<eos>' was not control-type; this is probably a bug in the model` → napomena o datoteci modela. Kod nas se pojavila i kod Gemme i kod Qwena, a modeli su nakon toga normalno odgovarali. Možeš je zanemariti.
:::

## Sažetak

Pokrenuti lokalni model znači preuzeti jednu datoteku i jedan program te izvesti jednu naredbu. Kod Gemme 4 E2B razmišljanje isključi s `-rea off` ili `--reasoning off` jer je inače potrošilo cijeli proračun od 256 tokena bez ijedne rečenice odgovora. `llama-server` nudi isti model kroz API u formatu OpenAI-ja, pa postojeću aplikaciju spajaš promjenom adrese. Izvještaj o brzini ima dva broja: prefill za čitanje i generiranje za pisanje. Na mjernom laptopu isti je model generirao između 5,6 i 12,1 tokena u sekundi, ovisno o alatu, zato izmjeri svoje. U sljedećem poglavlju otvaraš mapu modela.
