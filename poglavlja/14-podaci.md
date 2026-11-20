# Podaci

::: {.cilj}
**Nakon ovog poglavlja znaš:**

- kako izgleda jedan primjer za trening i što mu radi predložak
- odakle uzeti primjere i kako ukloniti osobne podatke
- zašto validacija na sintetičkim podacima laže i čemu služi zlatni skup
- što provjeriti prije nego što platiš prvi sat GPU-a
:::

U poglavlju 13 Kvaka je odlučila probati LoRA-u za zapisnike. Prirodno je odmah pitati za stopu učenja i broj epoha, a to dolazi u poglavlju 15. Podaci idu prije jer model uči točno ono što mu pokažeš, uključujući greške. Krivo označen primjer uči se jednako uredno kao točan, a gubitak pada na oba.

Naš mali podešeni model postigao je 81,7 % na validaciji i 43,8 % na zlatnom skupu. Uzrok te razlike leži u podacima, pa ga traži tamo prije nego što diraš postavke.

## Kako izgleda jedan primjer

Primjeri se obično spremaju kao **JSONL**: svaki redak datoteke jedan je cijeli JSON. Ovo je prvi redak `prilozi/podaci/train.jsonl`, ovdje prelomljen i sa skraćenom sistemskom porukom:

```json
{"messages": [
 {"role": "system", "content": "Ti si pomoćnik servisa Kvaka d.o.o.
   Iz zapisnika tehničara izvuci podatke i vrati samo JSON [...]"},
 {"role": "user", "content": "Kolega javlja s terena, perilica suđa
   voda stoji unutra, uzrok pumpa za izbacivanje. stranka nije u
   žurbi. SN 13A4582"},
 {"role": "assistant", "content": "{\"uredaj\": \"perilica posuđa\",
   \"kvar\": \"ne izbacuje vodu\", \"dio\": \"pumpa\",
   \"hitnost\": \"niska\"}"}
]}
```

To su iste tri uloge koje već poznaješ iz poglavlja 5. Svaka ima svoje pravilo:

- **System je isti kao u produkciji, znak po znak.** Puni tekst je u `prilozi/podaci/sustav.txt`. Ako ga kasnije doradiš, model dobiva ulaz koji nije vidio.
- **User je sirov ulaz.** Tipkarske pogreške, kratice i tekst bez dijakritika ostaju jer će takav tekst stizati i u produkciji.
- **Assistant je točno ono što želiš dobiti.** Model oponaša i sitnice: "Evo JSON-a:" u primjerima postaje "Evo JSON-a:" u odgovorima. Ključevi, redoslijed i oblikovanje neka budu uvijek isti.

Dopuštene vrijednosti propisuje `prilozi/podaci/shema.json`: četiri polja s popisom vrijednosti (`uredaj` 9, `kvar` 9, `dio` 13, `hitnost` 3) i zabrana drugih polja. Među dijelovima je i `nepoznato`. Model mora vidjeti primjere u kojima je to točan odgovor, inače će dio izmišljati kad ga zapisnik ne spominje. U našem treningu takvih je 21 od 240.

::: {.napomena}
Datoteke sadrže punu sistemsku poruku. Pokus iz poglavlja 16 radi sa skraćenom ("Iz zapisnika izvuci JSON s poljima uredaj, kvar, dio, hitnost.") jer na CPU-u svaki token košta vrijeme. Skraćena je ista u treningu i u ispitivanju, pa je pravilo poštovano. Puna ima 552 znaka, što je prema omjeru iz poglavlja 4 oko 170 do 240 tokena u svakom primjeru (gruba procjena).
:::

## Predložak: korak koji ne vidiš

JSONL nije ono što model čita. Poruke se najprije provlače kroz chat predložak (chat template) tog modela, a tek se dobiveni tekst tokenizira. Dekodiran, taj je primjer u našem pokusu sa SmolLM2 izgledao ovako (skraćeno):

```text
<|im_start|>system
Iz zapisnika izvuci JSON s poljima uredaj, kvar, dio, hitnost.<|im_end|>
<|im_start|>user
Kolega javlja s terena, [...] SN 13A4582<|im_end|>
<|im_start|>assistant
{"uredaj": "perilica posuđa", [...]}<|im_end|>
```

Ovdje je `add_generation_prompt` iz poglavlja 5 isključen jer odgovor već postoji u porukama. Oznaka `<|im_end|>` na kraju odgovora uči model kad treba stati.

Alat zato ne smije primijeniti neki svoj predložak. U Axolotlu se to piše ovako:

```yaml
chat_template: tokenizer_default
datasets:
  - path: podaci/train.jsonl
    type: chat_template
    ds_type: json
    field_messages: messages
```

::: {.neprovjereno}
Autor ovaj primjer nije pokrenuo jer Axolotl traži GPU. Nazivi ključeva mijenjaju se među inačicama, pa ih provjeri u dokumentaciji svoje inačice. Stariji recepti s `type: sharegpt` su zastarjeli, a ključevi `message_field_role` i `message_field_content` zamijenjeni su ključem `message_property_mappings`. U našim su podacima zadani nazivi `role` i `content`, pa ništa od toga ne treba. Cijelu konfiguraciju donosi poglavlje 16.
:::

Prije treninga pogledaj jedan primjer kao čisti tekst (poglavlje 5). Zamke su iste kao u tom poglavlju: SmolLM2 umeće svoju sistemsku poruku ako je tvoji podaci nemaju, a SmolLM3 svaki dan upisuje drugi datum.

## Odakle dolaze podaci

| Izvor | Prednost | Zamka |
|---|---|---|
| Stvarni zapisi | pravi jezik i pravi kvarovi | osobni podaci |
| Produkcijski logovi | isti ulazi kao u pogonu | odgovori starog modela nisu istina |
| Označavanje ljudi | najbolja kvaliteta | sporo, a ljudi se ne slažu |
| Označavanje LLM-om | brzo i jeftino | greške postaju "istina" |
| Sintetički podaci | bez osobnih podataka, koliko hoćeš | model nauči generator |

Logovi su privlačni jer već postoje, ali odgovor koji je tamo zapisan samo je ono što je stari sustav rekao. Ulaze uzmi, a odgovore ponovno provjeri.

**Označavanje LLM-om** (LLM-assisted labelling) izgleda kao da je zabadava: veliki model popuni odgovore, a ti ih samo prelistaš. Zamka je u tome što uredno napisana pogrešna oznaka ne upada u oči. Tvoj model zatim uči tuđe greške, a ako ga ocjenjuješ na oznakama istog LLM-a, mjeriš koliko se s njim slaže, a ne koliko je u pravu. Zato ljudi pregledavaju barem nasumičan uzorak, a zlatni skup označuju samo ljudi. Zapise anonimiziraj prije slanja vanjskom API-ju i pročitaj njegove uvjete (odjeljak o licencama niže).

### Anonimizacija

::: {.napomena}
Ovo nije pravni savjet. Za stvarne osobne podatke trebaju ti pravna osnova i jasna svrha po GDPR-u, a to provjeri sa službenikom za zaštitu podataka ili pravnikom. Ako čuvaš tablicu koja zamjene povezuje s pravim osobama, podaci su samo pseudonimizirani i i dalje su osobni.
:::

Model može zapamtiti i kasnije ponoviti dijelove primjera, pa osobni podatak ne smije ući u trening. Jednostavan popis:

- imena i prezimena, uključujući ona u sredini rečenice ("gosp. Ban")
- telefoni, e-adrese, OIB, IBAN
- adrese i kombinacije koje otkrivaju osobu (kvart, ulica i "starija gospođa")
- serijski brojevi, brojevi naloga i ugovora, ako vode do stranke
- opisi zdravlja i obiteljskih prilika, koji se znaju naći u slobodnom tekstu
- ručna provjera nasumičnog uzorka jer automatska zamjena promaši neobične oblike

Imena zamjenjuj izmišljenima, a oznake poput `[IME]` koristi samo ako će ih imati i produkcijski ulaz. U produkciji će zapisnici i dalje imati imena i kvartove, pa model treba vidjeti takav tekst da ih nauči zanemariti. Naš generator ima desetak naziva ulica na stalnim mjestima u predlošku, a slobodno spomenut kvart u rečenici nema. Posljedicu vidiš odmah.

## Naši podaci, otvoreno

Kvaka je izmišljena, pa stvarnih zapisnika nema. Skup je **sintetički** (synthetic data): skripta `l7_generiraj.py` slaže 240 zapisnika za trening i 60 za validaciju iz 12 predložaka i rječnika sinonima, a zatim dio teksta pokvari (bez dijakritika, zamijenjena slova, bez interpunkcije). Sjeme je 42, pa uvijek nastaju iste datoteke. Dva primjera:

```text
hl. / lupa u radu / treba zamijeniti vent. / srednje hitno
KVAR: propušta vodu. UREDJAJ: perilica rublja. NALAZ: uzrok manžeta.
PRIORITET: stranka nije u žurbi.
```

Zlatni skup od 40 zapisnika pisan je ručno, bez generatora, s duljim rečenicama i svakodnevnim jezikom:

```text
Vešmašina na Peščenici stane usred programa i bubanj ostane pun vode.
Začepljenja nema, filtar čist, motorčić pumpe ne reagira.
Dogovoreno za četvrtak.
```

### Pouka: 81,7 % prema 43,8 %

Na tim smo podacima podesili SmolLM2-135M-Instruct, malen model od 135 milijuna parametara (r = 8, 5 epoha, CPU, laptop i5-10210U, 16 GB, bez GPU-a). Validacijski gubitak pao je s 2,661 na 0,0628 i padao je do samog kraja, bez znakova prenaučenosti. Točnost nakon treninga, uz isti način generiranja i bez sheme:

| Skup | Valjan JSON | Točnost po polju | Cijeli zapisnik |
|---|---:|---:|---:|
| validacija (prvih 30) | 30/30 | 81,7 % | 15/30 |
| zlatni skup (40) | 39/40 | 43,8 % | 5/40 |

Prije treninga model nije dao nijedan valjan JSON, ni na jednom skupu. Oblik je dakle stvarno naučen, a značenje nije. Na gornji zapisnik iz Peščenice odgovorio je:

```json
{"uredaj": "peščenici", "kvar": "ne pali se", "dio": "motorči",
 "hitnost": "visoka"}
```

Točan je odgovor `perilica rublja`, `ne izbacuje vodu`, `pumpa`, `srednja`. Ni `Peščenice` ni `Vešmašine` u treningu nema, pa je model upisao riječ iz teksta koja mu je izgledala prikladno. Naučio je generator.

**Trigram riječi** je niz od tri uzastopne riječi. Koliko trigrama iz nekog skupa postoji i u treningu?

| Skup | Trigrami viđeni u treningu | Riječi po zapisniku |
|---|---:|---:|
| validacija | 41,1 % | 15,8 |
| zlatni skup | 0,5 % | 28,0 |

U treningu zapisnik ima prosječno 15,3 riječi. Bliskih duplikata između validacije i treninga nema, a ipak je gotovo pola trigrama zajedničko.

Validacija je iz iste tvornice kao trening. Ona iskreno mjeri koliko je model naučio tvornicu, a to te ne zanima. To je kao vježbati na poligonu i polagati ispit na istom poligonu: odličan rezultat ništa ne govori o prometu u gradu.

Odatle pravilo: **zlatni skup mora doći izvan procesa koji je napravio trening.** Kad je trening sintetički, zlatni skup čine stvarni zapisi ili ih barem piše čovjek koji generator nije vidio. Kad je trening stvaran, zlatni skup čine drugi zapisi, po mogućnosti iz novijeg razdoblja i od drugih stranaka.

Budimo pošteni i prema pokusu. Model je sitan, a zlatni su zapisnici dulji i teži, pa razliku ne možemo cijelu pripisati generatoru. Njihov je tekst ručno pisan za fiktivnu tvrtku, dakle i on je samo približan stvarnosti. Kvakin cilj od 90 % ovdje nije dosegnut. Sintetički podaci i dalje imaju korisnu ulogu: provjera cjevovoda, učenje oblika i dopuna rijetkih vrijednosti. Ne smiju biti jedini ispit.

## Koliko primjera

Ovo su pravila od oka, iskustvene polazne točke koje nismo izmjerili:

| Zadatak | Polazni broj primjera |
|---|---:|
| radi li cjevovod uopće | 20–50 |
| izvlačenje u stalnu shemu, kao Kvaka | 200–1000 |
| stil i ton kuće | 500–2000 |
| mnogo rijetkih kategorija ili teško razumijevanje | tisuće |

Izmjereni su samo krajnji slučajevi našeg pokusa, i to uz različite postavke: s 20 primjera gubitak je na treningu pao na 0,0011, a na validaciji stao na 0,59, dok je s 240 primjera bio 0,0374 prema 0,0628. Dvadeset primjera model zna napamet, a ni 240 iz iste tvornice nije donijelo uspjeh na zlatnom skupu. Broj ne zamjenjuje raznolikost.

Kreni malo i pogledaj **krivulju učenja** (learning curve): treniraj na četvrtini, polovici i cijelom skupu, a svaki put mjeri na zlatnom skupu. Ako rezultat raste, dodaj podatke. Ako je ravan, još istih primjera neće pomoći, pa traži drukčije primjere ili pregledaj oznake. Skripta `l9_trening.py` za to ima `--train-n`.

### Slažu li se ljudi

Prije velikog označavanja napravi mali test **slaganja označivača** (inter-annotator agreement). Dvije osobe neka neovisno označe istih 30 zapisnika, a ti za svako polje izračunaj postotak istih oznaka. Svako neslaganje pokazuje nejasnu uputu: kako označiti "treba odmah, ali stranka nije kod kuće"? Popravi upute i ponovi. Polje u kojem se ni ljudi ne slažu model neće naučiti dosljedno, a ni ocjena na njemu neće puno značiti.

Mi taj test nismo napravili, pa je to rupa u našim podacima. Upada u oči da je `hitnost` najslabije polje podešenog modela (14/40) i da je najslabija i kod Gemme sa shemom (26/40). Moguće je da je to najmutnije polje, ali to nismo provjerili.

## Podjela i provjere

Primjere dijeliš u tri skupa. **Validacijski skup** (validation set) prati trening, a zlatni ga ocjenjuje:

| Skup | Kvaka | Služi za | Mijenja težine |
|---|---:|---|---|
| trening | 240 | učenje | da |
| validacija | 60 | praćenje gubitka, odluka kada stati | ne |
| zlatni | 40 | konačna ocjena | ne, nikad |

Kod stvarnih podataka validaciji je dovoljno 10 do 20 % (također pravilo od oka). Najprije ukloni duplikate, a tek onda dijeli. Ako dugo prilagođavaš model dok ne prođe na zlatnom skupu, s vremenom i taj skup prestaje biti neovisan, pa ga povremeno obnovi.

### Curenje

**Curenje** (data leakage) znači da je model u treningu već vidio isto ili gotovo isto što ga čeka na validaciji, pa rezultat ispadne prelijep. Tri su uobičajena oblika:

- **Bliski duplikati:** isti tekst s drugim datumom ili brojem naloga. Prije usporedbe izbaci brojeve, dijakritike i veličinu slova.
- **Ista stranka ili isti tehničar:** jedan način pisanja završi s obje strane. Dijeli po stranci, a ne po retku. Još je bolje za validaciju uzeti najnovije razdoblje.
- **Isti generator:** ovo ne vidi nijedan alat za duplikate. Naša provjera to pokazuje: bliskih duplikata nema, a 41,1 % trigrama je zajedničko.

### Ravnoteža i duljina

Pogledaj koliko primjera ima svaka vrijednost. Za `hitnost` naši skupovi izgledaju ovako:

| Skup | niska | srednja | visoka |
|---|---:|---:|---:|
| trening | 78 | 73 | 89 |
| validacija | 16 | 25 | 19 |
| zlatni | 15 | 13 | 12 |

Generator hitnost bira jednoliko, a razlike su slučajne. Stvarni podaci rijetko su takvi. Ako je 90 % zapisnika `niska`, model koji uvijek kaže `niska` ima 90 % točnosti na tom polju i nikad ne prepoznaje hitan slučaj. Zato gledaj točnost i po vrijednosti, a rijetke vrijednosti obvezno neka budu u zlatnom skupu. Provjeri i ostala polja: dio `senzor` u našem treningu ima samo 2 primjera, a kvar `ne centrifugira` 5.

Druga je provjera duljina. Trening ima zadanu **najveću duljinu niza** (sequence length), u Axolotlu `sequence_len`, a mjeri se u tokenima. Primjer koji je prelazi alat može odrezati ili izbaciti. Odrezan primjer gubi upravo odgovor i token kraja jer su na kraju, pa model ne uči stati. Hrvatski je tu skup: u poglavlju 4 to je 2,25 tokena po riječi kod SmolLM3 i 2,70 kod SmolLM2. Zato broji tokene, svojim tokenizatorom i kroz predložak. Spremi kao `duljine.py`:

```python
import json, sys
from transformers import AutoTokenizer

t = AutoTokenizer.from_pretrained(sys.argv[1])
SUSTAV = open("podaci/sustav.txt", encoding="utf-8").read().strip()

def poruke(r):
    if "messages" in r:                  # train.jsonl i val.jsonl
        return r["messages"]
    return [                             # zlatni.jsonl: složi isti oblik
        {"role": "system", "content": SUSTAV},
        {"role": "user", "content": r["tekst"]},
        {"role": "assistant", "content": json.dumps(
            r["ocekivano"], ensure_ascii=False)}]

d = sorted(
    len(t(t.apply_chat_template(
        poruke(json.loads(red)), tokenize=False),
        add_special_tokens=False).input_ids)
    for red in open(sys.argv[2], encoding="utf-8"))
gr = int(sys.argv[3])
print("primjera", len(d), "prosjek", sum(d) // len(d),
      "p95", d[len(d) * 95 // 100], "najvise", d[-1])
print("dulje od", gr, ":", sum(x > gr for x in d))
```

```bash
python -X utf8 duljine.py HuggingFaceTB/SmolLM2-135M-Instruct \
  podaci/train.jsonl 512
python -X utf8 duljine.py HuggingFaceTB/SmolLM2-135M-Instruct \
  podaci/zlatni.jsonl 512
```

Skriptu pokreni iz radne mape jer čita `podaci/sustav.txt`. Zlatni skup nema poruke nego polja `tekst` i `ocekivano`, pa ih funkcija `poruke` slaže u isti oblik kao u treningu. Broj 512 samo je primjer granice. Stvaran ispis s punom sistemskom porukom, za train i zlatni skup (za Gemmu je tokenizator `google/gemma-4-E2B-it`):

| Tokenizator | Skup | Prosjek | p95 | Najviše | Preko 512 |
|---|---|---:|---:|---:|---:|
| SmolLM2 | train (240) | 356 | 376 | 385 | 0 |
| SmolLM2 | zlatni (40) | 384 | 402 | 408 | 0 |
| Gemma 4 E2B | train (240) | 277 | 290 | 298 | 0 |
| Gemma 4 E2B | zlatni (40) | 295 | 311 | 312 | 0 |

Nijedan primjer ne prelazi 512, pa na toj granici ništa ne bi trebalo biti odrezano. Gemmin tokenizator treba za iste primjere oko 22 % manje tokena od SmolLM2. S kratkom sistemskom porukom iz pokusa poglavlja 16 prosjek je kod SmolLM2 bio 132 tokena po primjeru, pa puna poruka trošak više nego udvostruči. Zlatni skup dulji je od treninga i u tokenima (384 prema 356 kod SmolLM2) i u riječima (28,0 prema 15,3), pa duljinu uvijek provjeri i na njemu.

### Provjera prema shemi

Skripta `l7_provjeri.py` broji primjere, ispisuje raspodjele po poljima, trigrame i točne duplikate, a prema shemi provjerava samo zlatni skup. Za svaki odgovor u treningu i validaciji treba ti još ova. Spremi je kao `odgovori.py`:

```python
import json, os, sys

m = sys.argv[1]
ucitaj = lambda ime: open(os.path.join(m, ime), encoding="utf-8")
shema = json.load(ucitaj("shema.json"))["properties"]
sustav = ucitaj("sustav.txt").read()
gresaka = 0

def provjeri(p):
    if [x["role"] for x in p] != ["system", "user", "assistant"]:
        return "uloge"
    if p[0]["content"] != sustav:
        return "sistemska poruka"
    if not p[1]["content"].strip():
        return "prazan ulaz"
    try:
        o = json.loads(p[2]["content"])
    except json.JSONDecodeError:
        return "nije JSON"
    if list(o) != list(shema):
        return "polja ili redoslijed"
    for k, v in o.items():
        if v not in shema[k]["enum"]:
            return f"{k}={v}"

for ime in ("train.jsonl", "val.jsonl"):
    n = 0
    for br, red in enumerate(ucitaj(ime), 1):
        n += 1
        g = provjeri(json.loads(red)["messages"])
        if g:
            gresaka += 1
            print(ime, "redak", br, g)
    print(ime, "primjera", n)
print("gresaka", gresaka)
```

Bliske duplikate, trigrame i ravnotežu ispisuje `sumnjivi.py`:

```python
import collections, json, os, re, sys, unicodedata

m = sys.argv[1]

def ucitaj(ime):
    r = []
    for red in open(os.path.join(m, ime), encoding="utf-8"):
        x = json.loads(red)
        if "tekst" in x:
            r.append((x["tekst"], x["ocekivano"]))
        else:
            p = x["messages"]
            r.append((p[1]["content"], json.loads(p[2]["content"])))
    return r

def kljuc(t):  # bez velikih slova, dijakritika, brojeva, interpunkcije
    t = unicodedata.normalize("NFD", t.lower().replace("đ", "d"))
    t = "".join(z for z in t if not unicodedata.combining(z))
    return " ".join(re.findall(r"[a-z]+", t))

def trigrami(t):
    w = re.findall(r"\w+", t.lower())
    return {tuple(w[i:i+3]) for i in range(len(w) - 2)}

tr, va, zl = map(ucitaj, ("train.jsonl", "val.jsonl", "zlatni.jsonl"))
K = collections.Counter(kljuc(t) for t, _ in tr)
print("bliski duplikati u train:", sum(n - 1 for n in K.values()))
print("val blizak train:", sum(kljuc(t) in K for t, _ in va))
A = set().union(*(trigrami(t) for t, _ in tr))
for ime, s in (("val", va), ("zlatni", zl)):
    u = [len(trigrami(t) & A) / max(1, len(trigrami(t))) for t, _ in s]
    print(f"trigrami {ime} u train: {sum(u) / len(u):.3f}")
for ime, s in (("train", tr), ("val", va), ("zlatni", zl)):
    c = collections.Counter(o["hitnost"] for _, o in s)
    print(ime, dict(sorted(c.items())))
```

## Licence podataka

Ni ovo nije pravni savjet.

- **Tvoji zapisi:** provjeri ugovore sa strankama i obveze povjerljivosti.
- **Javni skupovi:** svaki ima svoju licencu. NC isključuje komercijalnu upotrebu, a SA traži dijeljenje pod istim uvjetima. Vrijedi li to i za istrenirani model, pitanje je za pravnika.
- **Stranice s weba:** javno dostupno ne znači slobodno za upotrebu.
- **Izlazi LLM-a:** uvjeti komercijalnih API-ja često ograničavaju trening drugih modela njihovim izlazima, pa ih pročitaj. Kod modela otvorenih težina vrijedi treće pitanje iz poglavlja 9.

Podrijetlo svakog izvora zapiši u kratku datoteku uz podatke. Trebat će ti u poglavlju 19.

## Prije treninga

| Provjera | Kako | Kvaka |
|---|---|---|
| Osobni podaci uklonjeni | popis, uzorak ručno | izmišljeno, nema ih |
| Licenca i podrijetlo | zapis po izvoru | vlastito, generirano |
| System isti kao u produkciji | `odgovori.py` | da, 300/300 |
| Odgovori prema shemi | `odgovori.py` | da, 0 grešaka |
| Duplikati uklonjeni | `sumnjivi.py` | 0 točnih, 0 bliskih |
| Podjela bez curenja | po stranci, po vremenu | isti generator |
| Zlatni skup izvan procesa | izvor, trigrami | da, 0,5 % |
| Ravnoteža polja | raspodjele | rijetki: `senzor` 2 |
| Slaganje označivača | 30 zapisnika, dvije osobe | nije rađeno |
| Duljina u tokenima | `duljine.py` | najviše 408, 0 preko 512 |
| Predložak pogledan | ispis jednog primjera | da, SmolLM2 |

::: {.vjezba}
**Vježba: generiraj, provjeri, pregledaj** `CPU` · RAM 1 GB · disk 1 MB · 15 min

Radna mapa ima raspored iz `prilozi/README.md`. Skripte `odgovori.py` i `sumnjivi.py` spremi u `skripte`. Treba ti samo Python, bez dodatnih paketa.

1. Generiraj skup. Isto sjeme daje iste datoteke kao u prilozima, a prvi redak ispisa je `train 240 val 60`.

```bash
python -X utf8 skripte/l7_generiraj.py podaci
```

2. Provjeri ga. Ovo su retci ispisa koje tražiš:

```bash
python -X utf8 skripte/l7_provjeri.py podaci
```

```text
zlatni 40 train 240 val 60
sve vrijednosti zlatnog skupa su u shemi
udio trigrama rijeci zlatnog skupa koji postoje i u treningu:
  prosjek 0.005, najvise 0.045
rijeci po zapisniku, train: prosjek 15.3, min 10, max 25
rijeci po zapisniku, zlatni: prosjek 28.0, min 14, max 39
duplikati train+val: 0
```

3. Provjeri svaki odgovor i potraži curenje:

```bash
python -X utf8 skripte/odgovori.py podaci
python -X utf8 skripte/sumnjivi.py podaci
```

```text
train.jsonl primjera 240
val.jsonl primjera 60
gresaka 0
bliski duplikati u train: 0
val blizak train: 0
trigrami val u train: 0.411
trigrami zlatni u train: 0.005
train {'niska': 78, 'srednja': 73, 'visoka': 89}
val {'niska': 16, 'srednja': 25, 'visoka': 19}
zlatni {'niska': 15, 'srednja': 13, 'visoka': 12}
```

4. U prvom retku `podaci/train.jsonl` zamijeni `\"hitnost\": \"niska\"` sa `\"hitnost\": \"hitno\"` i ponovi `odgovori.py`. Ispis mora imati redak `train.jsonl redak 1 hitnost=hitno` i završiti sa `gresaka 1`. Ponovno pokreni prvi korak da vratiš datoteku.

5. Pročitaj očima 20 zapisnika iz treninga i 5 iz zlatnog skupa. Nađi ono što pravi tehničar ne bi napisao, poput `dio: vent..` ili `3.1.. mikrovalka`. Zatim napiši tri zapisnika svojim riječima i usporedi ih s treningom.

Brojevi iz koraka 2 i 3 ne ovise o stroju jer je sjeme zadano, a na tvojim podacima bit će drukčiji. Izmjeri svoje.
:::

::: {.kvar}
**Simptom → uzrok**

- Sjajno na validaciji, slabo na zlatnom skupu → model je naučio generator ili predloške. Vjeruj zlatnom skupu i dodaj raznolike stvarne primjere.
- U polju `uredaj` stoji dio adrese ili "gospa" → takvih smetnji nije bilo u treningu. Dodaj zapise s imenima i adresama, s izmišljenim vrijednostima.
- Odgovor počinje uvodom ili oznakom bloka koda → to je u primjerima ili se adapter nije aktivirao. Pregledaj odgovore i predložak.
- Model ne zna stati ili je JSON odrezan → token kraja nedostaje ili je primjer dulji od `sequence_len`. Pokreni `duljine.py` i pogledaj primjer kao tekst.
- Validacija bolja nego što je stvarnost dopušta → curenje: ista stranka ili bliski duplikati s obje strane. Dijeli po stranci i po vremenu.
- Polje uvijek dobiva istu vrijednost → neravnoteža. Mjeri točnost po vrijednosti i dodaj rijetke slučajeve.
- Model ponavlja ime ili telefon iz treninga → anonimizacija je promašila. Očisti podatke i treniraj ponovno jer se adapter ne može djelomično očistiti.
:::

## Sažetak

Primjer za trening je redak JSONL-a s tri poruke: sistemska je ista kao u produkciji, korisnička je sirov ulaz, odgovor je točno ono što želiš, a sve to model čita kroz vlastiti predložak. Osobne podatke ukloni prije svega ostalog i zapiši podrijetlo i licencu svakog izvora. Naš pokus pokazuje glavnu opasnost: na sintetičkoj validaciji 81,7 %, na zlatnom skupu 43,8 %, jer je model naučio generator, pa zlatni skup mora doći izvan procesa koji je stvorio trening. Prije treninga provjeri curenje, ravnotežu, duljinu u tokenima i svaki odgovor prema shemi, a broj primjera odredi krivuljom učenja. U poglavlju 15 slijedi što trening s tim podacima zapravo radi.
