# Tokeni

::: {.cilj}
**Nakon ovog poglavlja znaš:**

- što tokenizator radi s tekstom i zašto model čita tokene, a ne slova ili riječi
- koliko hrvatski košta u tokenima i kako to izmjeriti na vlastitom tekstu
- zašto se u ispisu pojavljuju slomljeni znakovi i zašto model ponekad ne zna stati
- zašto tokenizator pripada modelu i ne smije se zamijeniti drugim
:::

Token dosad poznaješ s računa: API naplaćuje po milijunu tokena, a razgovor ima ograničenje izraženo u tokenima. Izgleda kao mjerna jedinica, nešto poput kilovatsata. U stvarnosti je token ono što model doista čita. Čim to vidiš izbliza, računi i kvarovi postaju jasniji, a hrvatski se pokazuje skupljim nego što bi se reklo.

## Zašto ne slova i ne riječi

Model računa s brojevima. Svaka jedinica teksta mora imati redak u tablici brojeva, o čemu više u poglavlju 6. Tablica ima stalnu veličinu, pa je pitanje koliko su velike te jedinice.

Slova bi dala malu tablicu, ali predug niz. Model obrađuje jednu jedinicu u jednom koraku, a odlomak iz ovog poglavlja ima 872 znaka. Svako bi se značenje moralo graditi slovo po slovo.

Riječi bi dale kraći niz, ali tablica nikad ne bi bila dovoljna. Perilica, perilice, perilici, perilicu, perilicom, perilicama: šest redaka za jedan uređaj. K tome dolaze pogreške u tipkanju, imena, šifre dijelova i kod. Riječ koje nema u tablici model ne bi mogao ni pročitati.

Token je sredina između tih dvaju rješenja: komad teksta, dug od jednog bajta do cijele riječi. Česti nizovi dobiju jedan token, a rijetki se slažu od nekoliko. Tablica ostaje konačna, niz razumno kratak, a zapisati se može svaki tekst, u najgorem slučaju bajt po bajt.

## Tokenizator: stalni rječnik i ID-evi

**Tokenizator** (tokenizer) je program s rječnikom (vocabulary) komada teksta, u kojem svaki komad ima redni broj, **ID**. Rječnik se jednom nauči na tekstu za učenje i zatim se ne mijenja. Tokenizator radi dva posla:

- **kodiranje** (encode): tekst pretvara u niz ID-eva, i to prije nego što model išta vidi
- **dekodiranje** (decode): ID-eve koje model proizvede vraća u tekst

Model nikad ne vidi slova, samo brojeve. U mapi modela rječnik je u datoteci `tokenizer.json` (poglavlje 3), a u GGUF-u je ugrađen u samu datoteku (poglavlje 10). Starije upute spominju brzi (fast) i spori (slow) tokenizator: brzi čita `tokenizer.json`, a kod običnog korištenja razliku ne moraš pratiti.

### BPE običnim riječima

Najrašireniji postupak učenja rječnika zove se **BPE** (byte-pair encoding). Ideja stane u jednu rečenicu: prebroji koji se par susjednih komada najčešće pojavljuje, spoji ga u novi komad i ponavljaj dok rječnik ne naraste do željene veličine.

Probajmo na malom izmišljenom tekstu za učenje: `kvar` tri puta te `kvara`, `kvaru`, `kvaka` i dvaput `val`. Na početku je sve rastavljeno na slova.

| Korak | Najčešći par | Koliko puta | Novi komad |
|---|---|---:|---|
| 1 | `v` + `a` | 8 | `va` |
| 2 | `k` + `va` | 6 | `kva` |
| 3 | `kva` + `r` | 5 | `kvar` |

Nakon tri koraka `kvar` je jedan token, `kvara` je `kvar` + `a`, a `kvaka` je `kva` + `k` + `a`. Riječ koje u učenju nije bilo, recimo `kvarovi`, i dalje se može zapisati: `kvar` + `o` + `v` + `i`. Stvarni rječnici nastaju na isti način, ali na golemom tekstu i uz desetke tisuća spajanja, a kreću od bajtova umjesto od slova. U logu piše da je tokenizator SmolLM-a BPE. Drugi modeli mogu koristiti srodne postupke, a posljedica je ista: ono što je u tekstu za učenje bilo često postaje jedan token, a rijetko se raspada.

Odatle pravilo koje vrijedi za cijelo poglavlje: broj tokena ovisi o tome koliko je tvoj tekst sličan tekstu na kojem je rječnik učen.

## Kako se stvarno dijele hrvatske riječi

Evo stvarnih podjela četiriju tokenizatora iz modela koje koristimo u knjizi: SmolLM3-3B i SmolLM2-135M kroz `transformers`, Gemma 4 E2B i Qwen3-4B Q4_K_M kroz `llama-tokenize`. Razmak ispred riječi dio je prvog komada.

```text
popravak
  SmolLM3, SmolLM2, Gemma 4 (3)  ' pop' 'rav' 'ak'
  Qwen3 (4)                      ' pop' 'r' 'av' 'ak'
perilica
  sva četiri (2)                 ' peril' 'ica'
najnepredvidljivijih
  SmolLM3, Qwen3 (9)   ' naj' 'n' 'ep' 'red' 'vid' 'lj' 'iv' 'ij' 'ih'
  SmolLM2 (11)         ' n' 'aj' 'n' 'ep' 'red' 'vid' 'l' 'j' 'iv' 'ij' 'ih'
  Gemma 4 (7)          ' naj' 'nep' 'red' 'vid' 'ljiv' 'ij' 'ih'
čišćenje
  SmolLM3 (5)          ' či' 'š' 'ć' 'en' 'je'
  SmolLM2 (7)          ' �' '�' 'i' 'š' 'ć' 'en' 'je'
  Gemma 4 (4)          ' č' 'iš' 'ćen' 'je'
  Qwen3 (6)            ' č' 'i' 'š' 'ć' 'en' 'je'
```

Za usporedbu, engleski `washing` i `unpredictable` u sva četiri tokenizatora imaju po jedan token. Komadi poput `' pop'` i `'rav'` nemaju veze s popravkom, a `' peril'` je engleska riječ. Rječnik jednostavno nudi ono što ima.

Riječ bez dijakritika prolazi jeftinije. `cistenje` ima 3 tokena u SmolLM3, Gemmi i Qwenu, a 4 u SmolLM2, dok `čišćenje` istim redom ima 5, 4, 6 i 7. Nemoj iz toga zaključiti da treba brisati dijakritike. Mjerili smo samo broj tokena, a ne razumije li model takav tekst jednako dobro.

## Cijena hrvatskog: izmjereno

Uzmimo isti servisni odlomak o perilici na oba jezika. Počinje ovako:

> Kada perilica rublja stane usred programa i u bubnju ostane voda, prvo treba isključiti uređaj iz struje i zatvoriti dovod vode.
>
> When a washing machine stops in the middle of a programme and water remains in the drum, first unplug the appliance and close the water supply.

Hrvatska inačica kraća je u svakom pogledu koji se vidi okom: 141 riječ prema 172 i 872 znaka prema 993. Evo što kažu tokenizatori:

| Tokenizator | Alat | HR tokena | EN tokena | HR/EN |
|---|---|---:|---:|---:|
| SmolLM3-3B | transformers | 317 | 200 | 1,58 |
| SmolLM2-135M | transformers | 380 | 200 | 1,90 |
| Gemma 4 E2B Q4_K_M | llama-tokenize | 266 | 197 | 1,35 |
| Qwen3-4B Q4_K_M | llama-tokenize | 324 | 200 | 1,62 |

Isti sadržaj, manje riječi i manje znakova, a **1,35 do 1,90 puta više tokena**. Engleski je gotovo jednak u sva četiri rječnika, dok hrvatski ovisi o rječniku. Kod SmolLM3 to je 2,25 tokena po hrvatskoj riječi prema 1,16 po engleskoj, a kod SmolLM2 2,70 prema 1,16.

::: {.napomena}
Mjereno s transformers 5.22.1 i llama.cpp b12110 na laptopu i5-10210U, 16 GB, bez GPU-a. Broj tokena ne ovisi o stroju, ali ovisi o tekstu i rječniku. Ovo je jedan par tekstova: pokazuje smjer, bez statističke težine, i ne rangira tokenizatore. Rječnike ChatGPT-a, Claudea i Geminija nismo mjerili. Izmjeri svoje tekstove na svom modelu.
:::

### Koliko to stoji

**Novac.** API naplaćuje tokene, ulazne i izlazne. Ako se usluga koju koristiš ponaša kao ova četiri tokenizatora, ista količina posla na hrvatskom plaća se 1,35 do 1,90 puta više nego na engleskom. Kvaka to mora uračunati u cilj mjesečnog troška, a procjenu temeljiti na vlastitim zapisnicima.

**Mjesto u kontekstu.** Kontekst je ograničen brojem tokena, a to ograničenje podrobno obrađuje poglavlje 8. U 8192 tokena kod SmolLM3 stane 25 cijelih ovakvih odlomaka na hrvatskom i 40 na engleskom (izračun, bez predloška iz poglavlja 5). RAG iz poglavlja 13 time dobiva manje mjesta za dokumente.

**Brzina.** Model generira token po token, pa više tokena znači dulje čekanje. Gemma 4 E2B na mjernom laptopu generirala je između 5,61 i 12,06 tokena u sekundi, ovisno o alatu i trenutku. Pri toj brzini 266 tokena hrvatskog traje 22 do 47 s, a 197 tokena engleskog 16 do 35 s (izračun). Isti tekst, a razlika se osjeti. O brzini više u poglavlju 8.

### Rječnik je za hrvatski tanak

Postoji i cijena koja se ne vidi na računu. `unpredictable` je jedna jedinica s jednim retkom u tablici. `najnepredvidljivijih` je niz od 7 do 11 ulomaka koje model mora sam složiti u značenje. Iz ovih brojki zaključujemo da je hrvatskog u tekstu za učenje rječnika bilo malo, ali sastav tog teksta nismo mjerili.

Predviđa li model s takvim rječnikom hrvatski lošije od engleskog? To se može izmjeriti veličinom koja se zove perpleksnost, a do nje dolaziš u poglavlju 12. Tamo ćeš vidjeti i koliko hrvatski pati kad se model još i smanji.

## Mjeri, ne procjenjuj

Često se čuje pravilo "jedan token je oko 4 znaka". Na našem odlomku ono griješi u oba smjera:

| Jezik | Znakova | Procjena (znakovi / 4) | Stvarno tokena |
|---|---:|---:|---:|
| hrvatski | 872 | 218 | 266 do 380 |
| engleski | 993 | 248 | 197 do 200 |

Za hrvatski je pravilo preoptimistično: stvarno je jedan token 2,29 do 3,28 znakova (izračun). Zato tokene broji pravim tokenizatorom svog modela i na uzorku svog teksta. Za model u GGUF-u dovoljan je `llama-tokenize`, koji dolazi s llama.cpp, a kao izlaz daje popis ID-eva:

```bash
llama-tokenize -m MODEL.gguf -f tekst.txt --ids --no-bos --log-disable
```

`llama-server` u odgovoru vraća i `prompt_tokens` i `completion_tokens`, a slične brojeve obično vraćaju i komercijalni API-ji. Provjeri to u dokumentaciji svog pružatelja.

::: {.vjezba}
**Vježba: vidi svoje tokene** `CPU` · RAM 1 GB · disk 1 GB · 5 min

Treba ti paket `transformers`. Težine se ne preuzimaju, samo datoteke tokenizatora. Spremi kao `tokeni.py`. To je skraćena inačica skripte `prilozi/vjezbe/l3_tokeni.py`, a ona za cijeli pokus traži lokalne mape modela i `llama-tokenize`.

```python
import sys
from transformers import AutoTokenizer

t = AutoTokenizer.from_pretrained(sys.argv[1])
print("rječnik:", t.vocab_size, "s posebnima:", len(t))
print("posebni:", t.special_tokens_map)
for r in sys.argv[2:]:
    ids = t(r, add_special_tokens=False).input_ids
    print(repr(r), len(ids), [t.decode([i]) for i in ids])
    print("    ID:", ids)
```

Pokreni. U PowerShellu sve napiši u jedan redak, bez `\`. Oznaka `-X utf8` tjera Python na UTF-8 ispis jer na Windowsu ispis znaka `�` inače može završiti greškom.

```bash
pip install transformers
python -X utf8 tokeni.py HuggingFaceTB/SmolLM2-135M-Instruct \
  " popravak" " perilica" " čišćenje" " cistenje" " Zagreb" 2026
```

Vrijednosti iz našeg mjerenja, složene u obliku ovog ispisa, bez retka s posebnim tokenima i redaka s ID-evima:

```text
rječnik: 49152 s posebnima: 49152
' popravak' 3 [' pop', 'rav', 'ak']
' perilica' 2 [' peril', 'ica']
' čišćenje' 7 [' �', '�', 'i', 'š', 'ć', 'en', 'je']
' cistenje' 4 [' c', 'ist', 'en', 'je']
' Zagreb' 3 [' Z', 'ag', 'reb']
'2026' 4 ['2', '0', '2', '6']
```

Zatim probaj `" zagreb"`, `" ZAGREB"` i `"popravak"` bez razmaka, pa zamijeni model s `HuggingFaceTB/SmolLM3-3B` i usporedi. Upozorenje `Ignoring clean_up_tokenization_spaces=True` pojavilo se i kod nas i nije utjecalo na brojanje.
:::

::: {.drugacije}
Autor je ovu skraćenu skriptu pokrenuo s transformers 5.22.1 i s nazivom repozitorija (preuzeto je oko 20 MB datoteka tokenizatora) i s lokalnom mapom modela. Ispis je bio isti kao gore. Rad bez instaliranog `torch` nije provjeren.
:::

## Zamke pri dekodiranju

### Dijakritici razrezani preko tokena

Slovo `č` u UTF-8 zapisu zauzima dva bajta. Rječnik radi s bajtovima, pa ih SmolLM2 ne drži na okupu: u `čišćenje` su prva dva komada `' �'` i `'�'`. Nijedan od njih sam nije valjan znak, što možeš provjeriti u običnom Pythonu:

```python
b = "č".encode("utf-8")
print(list(b))                          # [196, 141]
print(b[:1].decode("utf-8", "replace")) # �
print(b.decode("utf-8"))                # č
```

Zato strujanje (streaming) ponekad pokazuje slomljene znakove. Model šalje token po token, a program koji svaki token dekodira zasebno ispiše `�` umjesto znaka koji stiže u dva dijela. Ispravan klijent drži nepotpune bajtove u međuspremniku dok znak ne bude cijeli. Ako `�` vidiš u gotovom, cijelom tekstu, a ne samo tijekom strujanja, uzrok je negdje drugdje, najčešće u kodiranju datoteke ili konzole.

### Razmak je dio tokena

`' pop'` s razmakom i `'pop'` bez njega različiti su komadi, svaki sa svojim ID-om. Riječ na početku reda i ista riječ usred rečenice mogu se zato podijeliti drukčije. Praktična posljedica: nemoj završavati prompt razmakom. Model bi sljedeću riječ normalno započeo tokenom s razmakom ispred, a taj je razmak već potrošen.

### Velika i mala slova

`Zagreb`, `zagreb` i `ZAGREB` za tokenizator su tri različita niza, pa mogu dati različit broj tokena i različite komade. Tekst pisan velikim slovima, kakav često dolazi iz starih sustava, računaj posebno.

Izmjereno na naša četiri tokenizatora, broj tokena po nizu (prva tri niza imaju razmak ispred, `popravak` nema):

| Tokenizator | ` Zagreb` | ` zagreb` | ` ZAGREB` | `popravak` |
|---|---:|---:|---:|---:|
| SmolLM2 | 3 | 3 | 4 | 3 |
| SmolLM3 | 2 | 2 | 4 | 3 |
| Gemma 4 | 1 | 2 | 4 | 3 |
| Qwen3 | 2 | 2 | 4 | 4 |

Velika slova koštaju najviše: `' ZAGREB'` kod sva četiri tokenizatora pada na komade `' Z'`, `'AG'`, `'RE'`, `'B'`. Gemma jedina ima `' Zagreb'` kao jedan token, a `' zagreb'` joj je već dva komada (`' zag'`, `'reb'`). Razmak mijenja komade, a ne uvijek i njihov broj: SmolLM2 `' popravak'` dijeli na `' pop'`, `'rav'`, `'ak'`, a `popravak` bez razmaka na `'pop'`, `'rav'`, `'ak'`. Isto je tri, ali su to drugi tokeni s drugim ID-evima. Qwen3 `popravak` bez razmaka razbija na četiri komada (`'pop'`, `'r'`, `'av'`, `'ak'`). Gemmu i Qwena brojali smo kroz `llama-tokenize`, SmolLM-ove kroz `transformers`.

### Brojevi

I ovdje se rječnici razlikuju. Za `2026` SmolLM3 daje `'202' '6'`, a SmolLM2 `'2' '0' '2' '6'`. Za `4,89` SmolLM3 daje `'4' ',' '89'`, a SmolLM2 `'4' ',' '8' '9'`. Gemma 4 i Qwen3 znamenke također ispisuju jednu po jednu, uz razmak koji je za njih dodala naša skripta, pa njihov ukupni zbroj od 5 tokena nije izravno usporediv s ostalima. Serijski broj u Kvakinu zapisniku zato kod takvih rječnika košta otprilike token po znamenci.

## Posebni tokeni

Dio rječnika nisu komadi teksta. **Posebni tokeni** (special tokens) oznake su strukture za model i program oko njega:

- **BOS** (begin of sequence) označava početak niza.
- **EOS** (end of sequence) je token kraja. Kad ga model proizvede, program prestaje generirati.
- **Oznake uloga** (role markers) kažu gdje počinje i završava čija poruka, npr. `<|im_start|>` i `<|im_end|>`.
- **PAD** popunjava kraće nizove kad se više njih obrađuje zajedno, u treningu i pri posluživanju.

Za model je takva oznaka jedan ID, bez ikakvih znakova `<`, `|`, `i`, `m`. Kod dekodiranja se često skriva, pa je u odgovoru ne vidiš iako je bila tamo. Zato smo u brojanju gore koristili `add_special_tokens=False` i `--no-bos`: htjeli smo samo tekst.

Modeli se ovdje jako razlikuju. SmolLM2 ima 17 dodanih tokena: `bos` je `<|im_start|>`, `eos` je `<|im_end|>`, a `unk` je `<|endoftext|>`. SmolLM3 ih ima 256, uključujući `<|begin_of_text|>`, `<think>` (ID 128002) i rezervirana mjesta za buduće oznake. Njegov popis navodi samo `eos` i `pad`, oba `<|im_end|>`.

Taj popis objašnjava čest kvar. Token kraja je običan izlaz modela koji program prepoznaje. Rječnik SmolLM3 sadrži i `<|end_of_text|>` i `<|eot_id|>`, a kao `eos` navodi `<|im_end|>`. Ako program čeka jedan, a model nauči ili iz predloška dobije drugi, generiranje se ne prekida. Model tada nastavlja pisati, često izmišlja i tuđe odgovore, dok ne stigne do `max_tokens`, a odgovor završi s `finish_reason: length`. Uzrok je najčešće u predlošku, koji je tema poglavlja 5. U logu llama.cpp ponekad vidiš i redak poput `control-looking token: 1 '<eos>' was not control-type`. Kod nas se pojavio za Gemmu i Qwena i nije zaustavio rad, ali ti govori gdje tražiti ako model ne staje.

## Tokenizator pripada modelu

Veličina rječnika određuje i oblik tablica u modelu. Tablica `model.embed_tokens.weight` ima po jedan redak za svaki ID, a završni dio modela, `lm_head`, daje po jedan broj za svaki ID. Oba dijela upoznaješ u poglavlju 6. Na našim modelima:

| Model | Veličina rječnika | `embed_tokens` |
|---|---:|---|
| SmolLM3-3B | 128 256 (128 000 + 256 posebnih) | 128256, 2048 |
| SmolLM2-135M | 49 152 (s posebnima) | 49152, 576 |

Primijeti da tokenizatorov `vocab_size` kod SmolLM3 javlja 128 000, a kod SmolLM2 49 152 zajedno s posebnima, dok `vocab_size` u `config.json` SmolLM3 iz poglavlja 3 ima 128 256. Zato s tablicom uspoređuj `len(tokenizator)`. Oba modela koriste istu tablicu za `embed_tokens` i `lm_head`, pa kod SmolLM3 u datoteci nema zasebnog `lm_head`, i to nije kvar.

ID ima značenje samo uz svoj rječnik. Kod SmolLM2 ID 2 je `<|im_end|>`, a u drugom rječniku isti je broj nešto sasvim drugo. Stoga vrijedi jedno tvrdo pravilo: **tokenizator i težine idu zajedno i nikad se ne miješaju**. Kriva kombinacija često ne javlja grešku. Model dobije valjane brojeve koji znače nešto drugo i odgovara besmislicama. Greška se javi tek ako ID ispadne iz tablice. Kad smo SmolLM2 dodali dva nova tokena bez proširenja tablice, log je zabilježio:

```text
BEZ resize_token_embeddings pada: IndexError index out of range in self
```

Dodavanje tokena obrađuje poglavlje 17. Tamo dolazi i Mergekit, gdje isto pravilo postaje zamka: ako spajaš modele s različitim rječnicima, glava pokazuje na krive tokene.

::: {.kvar}
**Simptom → uzrok**

- Računi za API veći su od procjene → procjena po znakovima ili riječima na hrvatskom. Izmjeri tokene na uzorku svog teksta.
- Dokumenti ne stanu u kontekst iako ih je "malo" → kontekst se mjeri u tokenima, a hrvatski ih troši više (poglavlje 8).
- `�` se pojavljuje tijekom strujanja, a u gotovom odgovoru ga nema → klijent dekodira token po token. Drži bajtove u međuspremniku dok znak ne bude cijeli.
- `�` je i u gotovom tekstu → kodiranje datoteke ili konzole. U Pythonu na Windowsu probaj `-X utf8`.
- Model ne staje i piše u tuđe ime, `finish_reason: length` → token kraja ne odgovara onome što program čeka. Provjeri predložak (poglavlje 5).
- U odgovoru se vidi doslovni `<|im_end|>` → posebni token ispisan je kao tekst, što je obično znak krivog predloška (poglavlje 5).
- `IndexError` s porukom `index out of range in self` → ID je veći od tablice embeddinga. Dodani su tokeni bez proširenja tablice ili je tokenizator od drugog modela.
- Model radi bez greške, ali odgovara besmislicama → provjeri potječe li tokenizator od tog modela.
:::

## Sažetak

Model čita tokene, komade teksta iz stalnog rječnika naučenog na tekstu za učenje, a tokenizator ih pretvara u ID-eve i natrag. Česti nizovi postaju jedan token, pa isti servisni odlomak na hrvatskom ima manje riječi i znakova, a 1,35 do 1,90 puta više tokena, što se plaća novcem, mjestom u kontekstu i vremenom. Zato tokene mjeri tokenizatorom svog modela, a pravilo od 4 znaka za hrvatski ostavi po strani. Razmaci, velika slova, brojevi i razrezani dijakritici objašnjavaju većinu čudnih ispisa, a pogrešan token kraja čest je razlog zašto model ne staje. Tokenizator i težine idu zajedno: veličina rječnika određuje oblik tablica `embed_tokens` i `lm_head`.
