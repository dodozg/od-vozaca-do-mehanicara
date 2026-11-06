# Brojevi u modelu

::: {.cilj}
**Nakon ovog poglavlja znaš:**

- pročitati oblik tenzora i iz njega izračunati broj parametara
- što znače znak, eksponent i mantisa te zašto svaki format bira između raspona i preciznosti
- po čemu se razlikuju FP16 i BF16 iako zauzimaju jednako mjesta
- napamet izračunati koliko će model zauzeti, bez zabune oko B, b, GB i GiB
:::

U poglavlju 6 motor je bio niz koraka: embedding, pažnja, MLP, logiti. Svi se ti koraci svode na množenje i zbrajanje brojeva, a težine na disku upravo su ti brojevi s imenima. Ako ih je 8 milijardi i svaki zauzima 2 bajta, to je 16 GB. Iz te jednostavne računice izlazi gotovo sve što slijedi u knjizi: stane li model u memoriju, koliko brzo radi i što žrtvuješ kad ga smanjuješ.

Zato u ovom poglavlju gledamo kako su brojevi složeni i kako je zapisan svaki pojedini.

## Tenzor i parametar

Težine (weights) složene su u imenovane tablice, svaka sa svojom namjenom. Takva tablica brojeva zove se **tenzor** (tensor).

Tenzor opisuju dva podatka. **Dimenzija** je jedan smjer u kojem se brojevi nižu. Popis ima jednu dimenziju, tablica s recima i stupcima dvije, a hrpa takvih tablica tri. **Oblik** (shape) kaže koliko je brojeva u svakom smjeru.

Uzmimo tenzor iz poglavlja 6, tablicu embeddinga modela Llama 3 8B. Taj model uzimamo samo za računicu jer su mu brojke javne:

```text
model.embed_tokens.weight    oblik [128256, 4096]
```

Dvije dimenzije, dakle tablica. Prva znači 128 256 redaka, po jedan za svaki token u rječniku. Druga znači 4096 stupaca, po jedan za svaku vrijednost u vektoru tog tokena. Ukupan broj vrijednosti u tenzoru uvijek je umnožak svih veličina iz oblika:

```text
128 256 × 4096 = 525 336 576
```

Drugi primjer je `model.layers.0.self_attn.q_proj.weight`, oblika `[4096, 4096]`, s 16 777 216 brojeva. Oznaka `layers.0` kaže da pripada prvom sloju, a isti tenzor postoji u svakom od 32 sloja.

Svaki od tih brojeva je **parametar** (parameter): vrijednost koju je odredio trening i koja se, spremljena u datoteci, pri pokretanju modela ne mijenja. Kad kažemo da model ima 8 milijardi parametara, mislimo na zbroj svih tih tablica.

Tenzori postoje i dok model radi. Poruka od 12 tokena prolazi kroz model kao tenzor oblika `[1, 12, 4096]`: jedna poruka, 12 tokena, 4096 vrijednosti za svaki. Ti brojevi nastaju računanjem i nestaju s njim, pa nisu parametri i ne ulaze u veličinu datoteke. Memoriju ipak troše, a to računamo u poglavlju 8.

## Kako se zapisuje jedan broj

Računalo ima samo bitove, a svaki broj dobiva ih ograničeno mnogo. Težina može biti 0,0213 ili −1,7, a tijekom računanja pojavljuju se i vrlo veliki i vrlo mali brojevi. Isti zapis mora podnijeti sve to.

Rješenje poznaješ iz škole, to je znanstveni zapis:

```text
6 500 000  =  6,5  × 10^6
0,0000213  =  2,13 × 10^-5
```

Svaki takav zapis ima tri dijela: **znak** (plus ili minus), **eksponent** (koliko je broj velik) i **mantisu** (njegove znamenke). Takav se broj zove broj s pomičnim zarezom (floating point) jer eksponent pomiče zarez.

Zamisli sada obrazac s fiksnim kućicama: jedna za znak, jedna za eksponent, tri za znamenke mantise. Takav obrazac doseže do 9,99 × 10^9^, gotovo deset milijardi. No 6 543 210 moraš upisati kao 6,54 × 10^6^, što znači 6 540 000. Ostatak se izgubi.

Iz tog obrasca slijede dva pojma na kojima stoji cijelo poglavlje:

- **Raspon** (range) govori koliko velik i koliko malen broj možeš zapisati. Određuje ga eksponent.
- **Preciznost** (precision) govori koliko su gusto raspoređeni brojevi koje možeš zapisati. Određuje je mantisa.

Primijeti još nešto. Oko broja 1 tvoj obrazac ima korak 0,01, a oko milijuna korak 10 000. Razmaci rastu s brojem, pa je pogreška zaokruživanja približno stalan postotak vrijednosti. Taj će nam postotak uskoro trebati.

Broj kućica je stalan, pa svaki bit dan eksponentu oduzimaš mantisi. Svi formati u ovom poglavlju samo su različite podjele tih bitova.

Računalo radi s bazom 2, pa je 6,5 zapisano kao 1,625 × 2^2^. U toj bazi mantisa uvijek počinje jedinicom, pa se ta jedinica ne sprema. Zato 7 spremljenih bitova mantise znači 8 značajnih bitova. Slika pokazuje kako svaki format dijeli svoje bitove.

![Raspored bitova za pet formata s pomičnim zarezom, u mjerilu](slike/bitovi.svg)

## Formati na jednom mjestu

Naziv formata kaže koliko bitova ima jedan broj: FP32 ima 32, FP16 ima 16. Osam bitova čini jedan bajt. Najčešće ćeš tražiti stupac "GB po milijardi": pomnoži ga brojem milijardi parametara i imaš veličinu težina.

| Format | Bitovi | Bajtovi po parametru | GB po milijardi | Gdje se koristi |
|:---|---:|---:|---:|:-----|
| FP32 | 32 | 4 | 4 | zbrajanje sitnih promjena u treningu |
| FP16 | 16 | 2 | 2 | starije kartice, pokretanje modela, KV cache |
| BF16 | 16 | 2 | 2 | izvorne težine, trening na novijim karticama |
| FP8 E4M3 | 8 | 1 | 1 | posluživanje na novijim karticama |
| FP8 E5M2 | 8 | 1 | 1 | trening, brojevi velikog raspona |
| INT8 | 8 | 1 | 1 | starija 8-bitna kvantizacija |
| 4-bit | 4 | 0,5 | 0,5 do 0,67 | GGUF Q4_K_M, QLoRA NF4, NVFP4 |

Oznake uz FP8 čitaju se doslovno: E4M3 znači 4 bita eksponenta i 3 mantise, a E5M2 znači 5 i 2. Isti broj bitova, druga podjela. E4M3 doseže do 448, a E5M2 do 57 344, ali u koracima dvostruko grubljim. Na FP8 se vraćamo u poglavlju 18.

INT8 i većina 4-bitnih formata rade drukčije i zato ih nema na slici. Spremaju cijeli broj s malo mogućih razina (256 za INT8, 16 za 4 bita) i jednu skalu zajedničku za cijelu skupinu brojeva. Vrijednost se dobiva množenjem razine i skale. Skale također zauzimaju mjesto, pa stvarna potrošnja izlazi iznad nazivne: README projekta llama.cpp za Q8_0 navodi 8,5 bita po težini, a za Q4_K_M 4,89. Kako se to radi i što se time gubi, tema je poglavlja 11.

## FP16 i BF16: isti trošak, druga slabost

I FP16 i BF16 imaju 16 bitova, pa model u njima zauzima jednako. Razlika je u podjeli, a ona pokazuje zašto format nije samo pitanje veličine.

| Format | Eksponent / mantisa | Najveći broj | Značajni bitovi |
|:---|:---|---:|---:|
| FP32 | 8 / 23 | 3,40 × 10^38^ | 24 |
| BF16 | 8 / 7 | 3,39 × 10^38^ | 8 |
| FP16 | 5 / 10 | 65 504 | 11 |

**FP16 ima usko grlo u rasponu.** Sve iznad najvećeg broja iz tablice prelazi u beskonačnost, a brojevi ispod otprilike 3 × 10^-8^ postaju nula. To su prelijevanje (overflow) i podlijevanje (underflow). U treningu se takvi brojevi stvarno pojavljuju, pa FP16 tamo traži dodatnu zaštitu koja se zove skaliranje gubitka.

**BF16 taj problem praktički nema.** Eksponent je isti kao u FP32, pa mu je raspon gotovo jednak i prelijevanje u praksi nije briga. Cijena je na drugoj strani: ima samo oko 8 značajnih bitova, što je dvije do tri dekadske znamenke. Mala promjena može se zaokružiti na ništa.

To možeš i izračunati. Trening, koji upoznaješ u poglavlju 15, pomiče težine u vrlo malim koracima, pa ovdje uzimamo težinu 1,0 i dodajemo joj malu promjenu u svakom formatu. Python nema BF16, ali ga je lako oponašati: to je FP32 zaokružen na gornjih 16 bitova.

```python
import struct

def fp32(x):
    return struct.unpack("<f", struct.pack("<f", x))[0]

def fp16(x):
    return struct.unpack("<e", struct.pack("<e", x))[0]

def bf16(x):
    # BF16 je FP32 bez donjih 16 bitova mantise: zaokruži i odreži.
    bits = struct.unpack("<I", struct.pack("<f", x))[0]
    gornji, donji = bits >> 16, bits & 0xFFFF
    if donji > 0x8000 or (donji == 0x8000 and gornji & 1):
        gornji += 1
    return struct.unpack("<f", struct.pack("<I", gornji << 16))[0]

formati = [("FP32", fp32), ("FP16", fp16), ("BF16", bf16)]

print("1,0 + promjena, jednom")
for promjena in (0.01, 0.001, 0.0001):
    for ime, f in formati:
        print(f"  {promjena:<7} {ime}  {f(1.0 + f(promjena)):.10f}")

print("1,0 + 0,001, 1000 puta (cilj je 2,0)")
for ime, f in formati:
    w = 1.0
    for _ in range(1000):
        w = f(w + f(0.001))
    print(f"  {ime}  {w:.6f}")
```

Stvarni izlaz (Python ispisuje decimalnu točku):

```text
1,0 + promjena, jednom
  0.01    FP32  1.0099999905
  0.01    FP16  1.0097656250
  0.01    BF16  1.0078125000
  0.001   FP32  1.0010000467
  0.001   FP16  1.0009765625
  0.001   BF16  1.0000000000
  0.0001  FP32  1.0001000166
  0.0001  FP16  1.0000000000
  0.0001  BF16  1.0000000000
1,0 + 0,001, 1000 puta (cilj je 2,0)
  FP32  2.000047
  FP16  1.976562
  BF16  1.000000
```

Pogledaj zadnji redak. Tisuću puta dodaješ 0,001 i težina se ne pomakne ni za dlaku. U BF16 je iznad 1,0 sljedeći mogući broj 1,0078125, što je korak od 1/128. Promjena manja od pola tog koraka zaokružuje se natrag na 1,0, pa se svaki put sve poništi. FP16 ima 8 puta manji korak i stiže do 1,98. Malo griješi jer 0,001 ni sam ne može zapisati točno.

Težina 1,0 je samo zgodan primjer. Stvarne su težine često mnogo manje, ali prag je postotak vrijednosti: u BF16 nestaje svaka promjena manja od otprilike 0,2 do 0,4 % vrijednosti težine, u FP16 granica je oko 0,02 do 0,05 %, a u FP32 oko 0,000006 %. Zato se u treningu brojevi koji skupljaju sitne promjene često drže u FP32. Otud prvi redak tablice.

Pri pokretanju modela težine se ne mijenjaju, pa se te sitne promjene nemaju gdje izgubiti i BF16 u toj ulozi dobro radi. Pitanje "koji format" zato uvijek znači i pitanje "što model s njime radi". Za spremanje i pokretanje BF16 je razuman izbor, a u treningu treba paziti na zaokruživanje.

::: {.vjezba}
**Vježba: gdje promjena nestaje** `CPU` · RAM i disk zanemarivi · 10 min

1. Spremi gornji kod kao `formati.py` i pokreni ga s `python formati.py`. Treba Python 3.6 ili noviji, bez dodatnih paketa.
2. U drugoj petlji zamijeni `0.001` sa `0.005` pa pokreni ponovno. Cilj je sada 6,0. FP32 daje 6.000091, a BF16 stane točno na 2.000000. Do 2,0 promjena prelazi pola koraka (1/256, oko 0,0039). Iznad 2,0 korak se udvostručuje, pola koraka raste na oko 0,0078 i promjena opet nestaje.
3. Dodaj redak `print(fp16(1e-9), bf16(1e-9))`. Vidjet ćeš da FP16 daje 0.0, a BF16 još drži broj.
:::

## NaN i Inf: brojevi koji nisu brojevi

Formati s pomičnim zarezom imaju i dva posebna zapisa:

- **Inf** znači beskonačno. Nastaje prelijevanjem, primjerice kad se u FP16 pojavi 70 000. Grafička kartica tu tiho zapiše Inf. Pythonov `struct` iz našeg primjera umjesto toga javi `OverflowError`.
- **NaN** (Not a Number) znači "ovo nije broj". Nastaje iz računa bez smislenog rezultata, kao što su 0 / 0 ili Inf − Inf.

NaN je zarazan jer svaki račun koji ga dotakne daje opet NaN:

```python
nan = float("nan")
inf = float("inf")
print(nan + 1, nan * 0, inf - inf, 0 * inf)
print(sum([1.0, 2.0, nan, 4.0]))
print(nan == nan)
```

```text
nan nan nan nan
nan
False
```

Sad se sjeti što model radi: množi tablice i zbraja retke. Svaka izlazna vrijednost u sloju zbroj je mnogih umnožaka, pa jedan NaN u jednoj težini pokvari cijeli zbroj. Sljedeći sloj prima pokvarene vrijednosti i širi ih dalje, a na kraju su i logiti NaN. Od milijardi brojeva dovoljan je jedan da model prestane davati smislen izlaz. U treningu je isto: kad gubitak jednom postane `nan`, zapis se više ne oporavlja, a spremljena datoteka nosi kvar sa sobom.

Zadnji redak izlaza ima praktičnu posljedicu: NaN nije jednak ni samom sebi, pa ga obična usporedba ne hvata. Treba ga posebno tražiti. Kako pregledati sve tenzore u modelu i pronaći takve brojeve, vidjet ćeš u poglavlju 17.

## Računica svakog mehaničara

Sad možeš izračunati veličinu težina bilo kojeg modela:

```text
broj parametara × bajtova po parametru = veličina

8 milijardi × 4 B    = 32 GB    (FP32)
8 milijardi × 2 B    = 16 GB    (BF16 ili FP16)
8 milijardi × 1 B    =  8 GB    (FP8)
8 milijardi × 0,61 B =  4,9 GB  (Q4_K_M, 4,89 bita po težini)
```

Provjeri to na stvarnom modelu: SmolLM3-3B ima 6,15 GB težina u safetensors formatu, a 6,15 / 2 daje oko 3,1 milijarde. Naziv "3B" zaokružen je, a 2 bajta po parametru slažu se s računicom. U poglavlju 8 ova računica postaje prvi pribrojnik formule za memoriju.

### Tri slova B

Isto slovo ovdje znači tri različite stvari:

- **8B** u nazivu modela znači 8 milijardi parametara. Dolazi od engleskog *billion*, što je hrvatska milijarda. Engleski *trillion* je hrvatski bilijun.
- **B** uz jedinicu je bajt: 16 GB, 2 B po parametru.
- **b** je bit, a jedan bajt ima 8 bitova. Internetska veza od 1 Gb/s prenosi 125 MB u sekundi, pa model od 16 GB putuje najmanje 128 sekundi. Kratica bpw (bits per weight) također broji bitove.

Dakle, model "8B" ima 8 milijardi parametara, a težine mu u BF16 zauzimaju 16 GB, što nema veze s osam bajtova.

### GB i GiB

Veličina datoteke može se brojati na dva načina. Proizvođači diskova, Hugging Face i ova knjiga koriste **GB**, što znači 10^9^ bajtova. Windows dijeli s 1024 × 1024 × 1024 = 1 073 741 824 bajta, što je zapravo **GiB**, ali ostavlja oznaku GB.

Zato model od 16 000 000 000 bajtova, kojemu na stranici piše 16 GB, u Windowsima pokazuje 14,9 GB. Ništa nije nedostajalo pri preuzimanju: 16 000 000 000 / 1 073 741 824 = 14,9. Razlika je oko 7 %. U ostatku knjige GB je uvijek decimalni, a GiB i MiB (1024 × 1024 bajtova) pojavljuju se samo kad citiramo izvor ili ispis alata koji ih koristi.

Stvarni primjer s našeg diska: `gemma-4-E2B-it-Q4_K_M.gguf` ima 3 106 738 272 bajta, što je 3,11 GB. Stupac Veličina u Windows Exploreru za nju je prikazao 2,89 GB (3 106 738 272 / 1 073 741 824 = 2,89). Qwen3-4B Q4_K_M ima 2 497 280 256 bajtova, što je 2,50 GB, a Explorer piše 2,32 GB. Datoteke su iste, različito je samo dijeljenje.

### Datoteka koja se udvostruči

README projekta llama.cpp za model Llama 3.1 8B navodi dvije brojke koje se na prvi pogled ne slažu: izvorna veličina 32,1 GB, a F16 14,96 GiB uz 16,0005 bita po težini. F16 je naziv koji llama.cpp koristi za FP16. Ako podijeliš 32,1 sa 14,96, dobiješ 2,15, a to je pogrešan račun jer su jedinice različite:

```text
14,96 GiB × 1,0737 = 16,06 GB
32,1 GB / 16,06 GB = 2,00
8,03 milijarde × 4 B = 32,1 GB
8,03 milijarde × 2 B = 16,06 GB
```

Nakon pretvorbe jedinica omjer je točno dvostruk. Iz same brojke ne možemo znati u kojem je formatu bila izvorna datoteka, ali 32,1 GB je upravo ono što daje 4 bajta po parametru.

Danas se težine najčešće objavljuju u BF16. Ponekad to piše već u nazivu repozitorija, kao kod `nvidia/NVIDIA-Nemotron-Labs-Dory1.0-4B-BF16`, a inače u kartici modela (model card). Ako naiđeš na FP32 inačicu istog modela koja je nastala iz BF16, datoteka je dvostruko veća, ali nosi iste vrijednosti: u našem kodu `bf16` donjih 16 bitova je nula, a odbačenu preciznost pretvorba ne vraća. Isto vrijedi i za kvantizaciju u poglavlju 11, pa se uvijek kreće od najpreciznije datoteke koju imaš.

U poglavlju 15 susrećeš još jedan 4-bitni format, NF4 iz QLoRA-e. On služi treningu i nije isto što i GGUF.

::: {.kvar}
**Simptom → uzrok**

- Preuzeti model od 16 GB u Windowsima pokazuje 14,9 GB → GB i GiB. Datoteka je cijela; usporedi broj bajtova ili hash.
- Datoteka je dvostruko veća od računice s 2 B po parametru → vjerojatno je u FP32. Provjeri format u kartici modela prije nego što pretpostaviš da je to drukčiji model.
- Gubitak u treningu odjednom postane `nan` → prelijevanje ili nedopušten račun. Provjeri format i stopu učenja (poglavlja 15 i 16).
:::

## Sažetak

Model je skup imenovanih tenzora, a broj parametara u svakome je umnožak njegova oblika. Svaki parametar zapisan je znakom, eksponentom i mantisom: eksponent daje raspon, mantisa preciznost, a bitovi se dijele između njih. FP16 ima usko grlo u rasponu, dok BF16 ima raspon gotovo kao FP32, ali s oko 8 značajnih bitova može zaokružiti male promjene na ništa. Jedan NaN može onesposobiti cijeli model. Veličinu težina računaš kao parametri × bajtovi, pri čemu 8B znači milijarde, a Windows prikazuje GiB s oznakom GB.
