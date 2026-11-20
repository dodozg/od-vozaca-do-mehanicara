# Cijeli put

::: {.cilj}
**Nakon ovog poglavlja znaš:**

- proći cijeli put od cilja do pogona i na svakom koraku reći što je izmjereno
- pronaći kvar preko jedne tablice simptoma
- provjeriti sustav prije puštanja u rad, uključujući licence, podatke, sigurnost i AI Act
- čitati nove arhitekture, poput modela s petljama, istim alatima
:::

U poglavlju 1 Kvaka d.o.o. zapisuje tri granice: točnost po polju od barem 90 %, p95 latenciju do 5 s i najviše 150 EUR mjesečno. Sada prolazimo sve odluke redom, svaku s izmjerenim brojem. Kvaka je izmišljena, kao i njezini podaci i cijene, a mjerenja su stvarna, s laptopa i5-10210U sa 16 GB RAM-a i bez GPU-a (llama.cpp b12110). Tvoje će brojke biti drukčije.

Unaprijed kažemo kako priča završava: **na ovom laptopu ciljevi nisu dosegnuti.** Najbolja točnost je 74,4 %.

## Kvaka od početka do kraja

![Cjevovod od cilja i mjera preko modela, prompta i RAG-a, podataka, treninga, spajanja, pretvorbe, kvantizacije, mjerenja i sigurnosti do posluživanja i pogona, s povratkom na podatke i trening kad je rezultat ispod cilja](slike/cijeli-put.svg)

### Cilj i zlatni skup (poglavlja 1 i 9)

Kvaka najprije određuje što znači "gotovo", a zatim ručno označava 40 zapisnika koji nikad ne ulaze u trening. To je 160 polja, pa jedno polje vrijedi 0,625 boda. Cilj od 90 % znači 144 točna polja. Razlike od nekoliko polja na tako malom skupu ništa ne dokazuju, što se vidi do kraja puta.

### Izbor modela (poglavlja 2, 8 i 9)

Oba kandidata imaju licencu Apache 2.0 i rade na laptopu. Gemma 4 E2B u datoteci od 3,11 GB treba oko 2650 MiB memorije i prefill od 71 do 88 tokena u sekundi. Qwen3-4B u datoteci od 2,50 GB treba oko 4720 MiB, a prefill mu je 16 do 20 tokena u sekundi. Kvaka uzima Gemmu.

Qwen je naknadno prošao zlatni skup: 66,2 % (106/160), isto sa shemom i bez nje, 4/40 cijelih zapisnika, `hitnost` 19/40. Gemma sa shemom ima 74,4 %, pa je odluka potvrđena i točnošću, a ne samo memorijom i brzinom. Razlika od 13 polja na 40 zapisnika ipak je mala.

### Prva osnovica: prompt (poglavlja 9 i 13)

Gemma Q4_K_M, sistemska poruka s dopuštenim vrijednostima, `--reasoning off`, temperatura 0. Rezultat je **71,25 %**, 11 od 40 cijelih zapisnika, p95 7,9 s. JSON je valjan u svih 40 odgovora, a među njima stoji i `"dio": "guma"`, vrijednost koje nema na popisu. Da je Kvaka brojala samo valjan JSON, ovdje bi stala i proglasila uspjeh.

### Shema (poglavlje 13)

Ista poruka uz JSON shemu daje **74,4 %**, 12 od 40 cijelih zapisnika, p95 6,7 s. To je 119 od 160 polja, dakle 25 premalo. Razlika prema promptu iznosi 5 polja, što je premalo za zaključak. Shema uklanja vrijednosti izvan popisa, a značenje ne popravlja: `hitnost` ostaje na 26/40 u oba načina. Ovih 74,4 % ostaje najbolji rezultat u cijeloj knjizi.

Sljedeći najjeftiniji korak bio je dopuniti poruku definicijama jer svih 14 grešaka u hitnosti ide stupanj naviše, a poruka vrijednosti samo nabraja. Izmjereno: poruka s definicijama hitnosti iz vježbe u poglavlju 13 daje 118 od 160 polja (73,8 %) i `hitnost` 26/40, dakle isto kao polazna (119/160 i 26/40). Prompt time nije dosegnuo cilj.

### RAG za priručnik (poglavlje 13)

Pitanja iz priručnika su drugi posao, s drugim alatom. Priručnik je razrezan na 15 komada, a bge-m3 nalazi točan komad među prva tri za 7 od 7 pitanja. Gemma daje 7 prihvatljivih odgovora od 8. Promašaj je poučan: na pitanje o cijeni izlaska i dva sata rada navodi obje stavke, a zbroj od 145 eura izostaje. Račun zato prepuštamo kodu.

Dvije stvari ostaju otvorene. Sličnost je oko 0,77 i za pitanje bez odgovora u priručniku, pa odbijanje ovisi o uputi i navodu izvora. Podmetnuta naredba ne prolazi uz istinit komad (0/12), a prolazi kad je sama u kontekstu (6/6). Odgovor traje 3,5 do 11,1 s. Na osam pitanja to je raspon, a p95 se iz njih ne može pošteno izračunati.

### LoRA za zapisnike (poglavlja 14 do 16)

Ispod 90 % poglavlje 13 upućuje na LoRA-u. Ovdje put postaje manje uredan od slike. Trening baze veličine Gemme na laptopu nije pokušan jer već kod malog modela korak traje oko 5 s, a pravi trening na najmljenom GPU-u autor nije pokrenuo. Na CPU-u je treniran SmolLM2 s 135 milijuna parametara: 240 sintetičkih primjera, r = 8, 921 600 parametara za trening (0,680 %), 1531 s, najbolji validacijski gubitak 0,0628, adapter od 3,72 MB u FP32.

Prije treninga model na zlatnom skupu ima 0,0 %, poslije **43,8 %**. Na sintetičkoj validaciji isti model ima 81,7 %. Taj jaz je najvažniji broj u ovom dijelu puta: model je naučio generator podataka, pa u polje `uredaj` upisuje "gospa" i "peščenici". Oblik je naučen, vrijednosti nisu.

### Spajanje, pretvorba i kvantizacija (poglavlja 11 i 16)

Adapter se spaja u bazu i sprema u FP16 (269 060 280 B), a pretvorba daje F16 GGUF od 270 885 824 B. Spojeni model i model s adapterom daju isti odgovor na jedan probni prompt. Logiti se razlikuju najviše za 0,09, a najvjerojatniji token isti je na svih 1214 položaja prvih 10 zapisnika zlatnog skupa (poglavlje 16). Sve razine idu izravno iz F16 mastera:

| Razina | Datoteka | Točnost, shema | Cijeli zapisnici |
|---|---:|---:|---:|
| bazni model, F16 | nije zapisano | 16,9 % | 0/40 |
| LoRA, Q8_0 | 144,8 MB | 45,6 % | 5/40 |
| LoRA, Q4_K_M | 105,5 MB | 44,4 % | 5/40 |
| LoRA, Q2_K | 88,2 MB | 25,6 % | 0/40 |

### Mjerenje štete (poglavlje 12)

Kvaka toleranciju zapisuje unaprijed: najviše 5 polja ukupno i najviše 3 u jednom polju, u odnosu na referencu. Q4_K_M prolazi s 2 polja manje. Q2_K pada jer `kvar` gubi 16 od 40, dok JSON ostaje valjan 40/40. Perpleksnost to najavljuje za hrvatski, izmjereno na SmolLM3: Q2_K je diže s 19,77 na 58,80, a na engleskom sa 7,08 na 12,88, na samo tri komada teksta.

Ovaj korak kaže samo da Q4_K_M nije krivac za loš rezultat. Adapter sa 44,4 % ostaje daleko od 90 % i ne može se pošteno usporediti s Gemmom: to je mnogo manji model, a dobio je skraćenu sistemsku poruku. Kvakin najbolji kandidat ostaje Gemma sa shemom, bez adaptera. Datoteka koju bi Kvaka danas isporučila uopće nema LoRA-e.

### Posluživanje (poglavlja 8 i 18)

`llama-server` s Gemmom Q4_K_M i zahtjevom od 48 tokena:

| `-np` | Klijenata | Prvi token, p50 | Latencija p95 | Ukupno tok/s |
|---:|---:|---:|---:|---:|
| 1 | 1 | 0,57 s | 4,78 s | 10,23 |
| 1 | 4 | 14,31 s | 18,77 s | 10,4 |
| 2 | 4 | 9,12 s | 16,29 s | 12,34 |
| 4 | 4 | 4,91 s | 13,36 s | 14,61 |

Jedan klijent ulazi u 5 s, s malom rezervom i na samo dva zahtjeva, a zapisnik iz zlatnog skupa, s odgovorom od oko 60 tokena, ima p95 od 6,7 s. Četiri klijenta ne ulaze ni u jednoj postavci. Veći `-np` skraćuje čekanje na prvi token, ali klijentu smanjuje brzinu, s 11,13 na 5,7 tokena u sekundi. Ovdje je p95 izračunat na najviše 8 zahtjeva, pa je to gruba slika. Ovaj test zadaje `-c 8192`, što kod `-np 4` daje 2048 tokena po klijentu; za puni kontekst od 8192 svakome trebao bi `-c 32768`.

### Pogon (poglavlje 18)

Ovaj korak nije izveden: laptop nije pogon, a Kvaka ne postoji. Pravi sustav redovito bilježi p95, vrijeme do prvog tokena, duljinu reda čekanja i udio odgovora s `finish_reason: length`. Bilježi i inačicu modela i predloška uz svaki zahtjev te povremeno ručno ocjenjuje uzorak stvarnih odgovora. Zapisnici pogona također mogu sadržavati osobne podatke.

### Gdje Kvaka stvarno stoji

| Cilj | Granica | Najbolje izmjereno | Stanje |
|---|---:|-------|---|
| Točnost | ≥ 90 % | 74,4 % (119/160) | nije dosegnut |
| p95, zapisnik | ≤ 5 s | 6,7 s, jedan po jedan | nije dosegnut |
| p95, 4 klijenta | ≤ 5 s | 13,36 s | nije dosegnut |
| Trošak | ≤ 150 EUR | vidi niže | ovisi o putu |

Trošak nije mjeren. Račun iz poglavlja 1 počiva na izmišljenim ulazima i kaže da prolazi samo API, s 32,44 EUR, dok vlastiti stroj (213,48 EUR) i stalni najam (224 EUR) ne prolaze. Najam od 22 sata mjesečno (136 EUR) prolazi samo ako zapisnici mogu čekati. Laptop na kojem je sve izmjereno nije ni u tom računu, a nijedan API model nije mjeren na Kvakinom zlatnom skupu. Dakle ne znamo postoji li put koji istodobno zadovoljava sva tri cilja.

Sljedeći koraci, od najjeftinijeg:

1. **Bolja poruka**, posebno za `hitnost`. Definicije nisu pomogle, pa probaj primjere ili drukčije pravilo. Jedan prolaz zlatnog skupa traje oko 4 minute (235 s). Možda ni ljudi nemaju jasno pravilo, pa ga prvo dogovori s njima.
2. **Drugi modeli na istom skupu:** SmolLM3 i jedan API model kao gornja referenca. Qwen3-4B već je izmjeren i slabiji je od Gemme.
3. **Stvarni zapisnici**, očišćeni prema poglavlju 14, jer jaz od 81,7 % prema 43,8 % govori da su podaci najveća rupa.
4. **QLoRA na bazi veličine Gemme,** na najmljenom GPU-u, uz shemu. LoRA tada ne uči oblik i može se baviti navikama. Jamstva nema jer je preostalih 25 polja uglavnom pogreška u značenju.
5. **Jači stroj ili skupna obrada** za latenciju, s novim računom troška. Ni tada se ne preskače zlatni skup.

Ako ni to ne uspije, ostaju tri poštene odluke: niži cilj, čovjek provjerava nesigurne zapisnike ili odustajanje od projekta. Svaka je valjan rezultat, a mogu se braniti zato što su brojke zapisane. Dobar mehaničar kaže i kad auto neće proći tehnički pregled.

## Pravila koja vrijede na svakom koraku

- **Čuvaj master.** Težine u F16 ili BF16 i izvorni adapter ne brišeš nakon kvantizacije.
- **Nikad ne kvantiziraj kvantizirano.** Svaka razina nastaje izravno iz mastera.
- **Isti predložak u treningu i posluživanju.** Uspoređuješ prikazani niz i broj tokena prompta.
- **Zlatni skup nakon svake promjene.** Model, razina, predložak, poruka, inačica alata.
- **Uspoređuj samo jednako s jednakim.** Isti skup, ista poruka, iste postavke. PPL samo unutar istog modela na istom tekstu.
- **Prikvači revizije.** Hash commita i SHA256 datoteke, inačice alata u `pip freeze`.
- **Ne vjeruj "valjanom JSON-u".** Gledaj točnost po polju i čitaj odgovore.
- **I predlošci su kod.** Čitaš ih, pregledavaš i verzioniraš kao svaki drugi program koji izvršavaš.

## Stablo kvarova

Kreni od simptoma, pogledaj navedeno mjesto, a u poglavlju su popravak i izmjereni primjer. Većina ovih kvarova ne javlja grešku.

| Simptom | Gdje gledati | Pogl. |
|-----|-----|--|
| Prazan odgovor, `length`, popunjen `reasoning_content` | razmišljanje i `max_tokens` | 2, 5 |
| Prazan odgovor, `stop`, jedan token | kraj predloška, `add_generation_prompt` | 5 |
| Odgovor bez veze s pitanjem, malen `prompt_tokens` | `/apply-template`, `--chat-template` | 5 |
| Model ne staje ili ispisuje posebni token | token kraja, predložak druge obitelji | 4, 5 |
| Model nastavlja tvoje pitanje | predložak se ne primjenjuje, bazni model | 3, 5 |
| Besmislica i na temperaturi 0 | tokenizator, predložak, datoteka, razina | 4, 6, 10, 11 |
| Rečenica ili poveznica koju nitko nije tražio | predložak, podmetnuta naredba, navod izvora | 5, 10, 13 |
| Greška zaglavlja, datoteka 0 B | `hf cache verify`, lokalni disk | 10 |
| Isti naziv modela, drukčiji rezultati | pomaknut `main`, prikvači commit | 10 |
| Isti `seed`, drukčiji odgovor | uzorkovanje, prompt cache | 2, 6 |
| Puca kad povećaš `-c` | KV cache, račun memorije | 8 |
| Uz `-np` poruke prelaze kontekst | `-c` se dijeli na slotove | 8 |
| Prvi token kasni | prefill, red čekanja | 8, 18 |
| Tekst puže, a GPU postoji | `offloaded N/M`, CPU paket | 8 |
| Valjan JSON, niska točnost | točnost po polju, čitanje odgovora | 9, 12, 13 |
| Odlična validacija, slab zlatni skup | podaci ne liče na stvarnost | 14, 16 |
| Nizak gubitak treninga, ravan i visok val | prenaučenost, ranija spremljena točka | 15, 16 |
| `NaN` ili gubitak se ne miče | stopa učenja, format, ciljni moduli | 7, 15 |
| Dobro na adapteru, loše nakon GGUF-a | predložak, sistemska poruka, razina | 5, 12, 16 |
| Nakon kirurgije tih pad kvalitete | slojevi i `config.json`, strogo učitavanje | 3, 17 |

## Kontrolna lista prije puštanja u rad

### Ciljevi i mjerenje

- Točnost, p95 i trošak izmjereni su na datoteci koja se isporučuje, a ne na njezinoj prethodnici.
- Test opterećenja odgovara stvarnom prometu i stvarnoj duljini zahtjeva.
- Kapacitet je provjeren prema računu iz poglavlja 1, uključujući tvoje sate.
- Postoji odluka što se radi s rezultatom ispod cilja i tko provjerava odgovore u koje se ne može vjerovati.

### Licenca (poglavlje 9)

- Tekst licence pročitan je za točnu inačicu modela, a ne prema kartici ili članku.
- Znaš što moraš učiniti kad dijeliš podešeni model ili proizvod s njim.
- Podrijetlo i licenca svakog izvora podataka zapisani su u datoteci iz poglavlja 14.

### Podaci i GDPR (poglavlja 1 i 14)

Ovo nije pravni savjet.

- Za osobne podatke postoje pravna osnova, svrha i rok čuvanja, a ostaješ voditelj obrade i na vlastitom stroju.
- S izvršiteljem obrade postoji ugovor, a prijenos izvan EGP-a je provjeren.
- Osobni podaci uklonjeni su prije treninga jer se adapter ne može djelomično očistiti.
- Zapisnici pogona imaju rok čuvanja i kontrolu pristupa.

### Sigurnost (poglavlja 5, 10 i 13)

- Težine su u safetensors ili GGUF formatu; `.bin` i `.pt` učitavaš samo u izolaciji.
- `trust_remote_code` je isključen ili je kod pročitan i prikvačen na commit. Isto vrijedi za pretvorbu jer `convert_hf_to_gguf.py` za neke arhitekture izvršava kod iz repozitorija.
- Model je preuzet iz službenog repozitorija, a SHA256 je provjeren.
- Chat predložak je pročitan i uspoređen s izvornikom. Skeniranje na Hugging Faceu ne analizira logiku predložaka (arXiv 2602.04653).
- Poslužitelj ima API ključ i nije otvoren prema internetu.
- Dokumenti u RAG-u smatraju se nepouzdanim ulazom: navod izvora, pitanja bez odgovora i pokus s podmetnutom naredbom. Alat koji model predloži izvodi tvoj kod, s najmanjim potrebnim ovlastima.

### Sigurnost nakon finog podešavanja (poglavlje 16)

Fino podešavanje može oslabiti odbijanja i na bezazlenim podacima. Isti popis od oko 20 upita pusti kroz bazu i kroz datoteku koju isporučuješ: odbijanja, poruke izvan posla, podmetanje i curenje podataka iz treninga. Ako baza odbije, a podešeni model odgovori, isporuka čeka dok ne doznaš zašto.

### AI Act

Ovo nije pravni savjet. Podaci su stanje u studenom 2026., a dio dolazi iz sekundarnih izvora. **Provjeri ih prije nego što se osloniš na njih,** s pravnikom ako o tome ovisi posao.

- **Podešavanje.** Prema smjernicama za modele opće namjene iz srpnja 2025., onaj tko podešava model postaje pružatelj novog modela samo ako bitno promijeni njegovu općenitost, sposobnosti ili sustavni rizik. Orijentir je više od trećine računalnih resursa utrošenih na trening izvornog modela. Ako taj podatak nije poznat, uzima se trećina od 10^23^ FLOP, a za model sa sustavnim rizikom trećina od 10^25^ FLOP. I tada se obveze u pravilu ograničavaju na samu izmjenu, osim što izmjena modela sa sustavnim rizikom može povući i obveze za takve modele.
- **Rokovi, prema sekundarnim izvorima.** Digitalni omnibus, Uredba (EU) 2026/1744, na snazi je od 27. 7. 2026. Visokorizični sustavi iz Priloga III odgođeni su na 2. 12. 2027., a oni ugrađeni u proizvode na 2. 8. 2028. Članak 50 i ovlasti AI Officea nad modelima opće namjene primjenjuju se od 2. 8. 2026., uz prijelazni rok do 2. 12. 2026. za označavanje generiranog sadržaja kod sustava koji su već na tržištu.
- **Što ostaje na tebi.** Pravilo o podešavanju govori o modelu, a tvoj sustav i dalje procjenjuješ prema namjeni. Zapiši koliko je računanja trening stvarno trošio i spada li sustav u Prilog III.

## Što dolazi: modeli s petljama

Nova ideja dobra je provjera znaš li još čitati model, pa uzmimo jednu. U poglavlju 6 token kroz svaki sloj prolazi jednom. **Modeli s petljama** (looped) isti dio mreže prolaze više puta.

![Dory1.0-4B: ulazni blok, ponavljajući blok N puta i izlazni blok, uz ponovno ubacivanje ulaza u svaku petlju](slike/looped.svg)

NVIDIA Dory1.0-4B objavljena je 16. 10. 2026. (`nvidia/NVIDIA-Nemotron-Labs-Dory1.0-4B-BF16`, uz inačice `-GGUF` i `-NVFP4`), pod licencom OpenMDW-1.1 (poglavlje 9). Ima 4 milijarde parametara, raspoređenih u 8 ulaznih, 20 ponavljajućih i 8 izlaznih blokova. Ulaz se ponovno ubacuje u svaku petlju. Čitaš li `config.json`, nemoj se zbuniti: on pažnju i MLP broji odvojeno, pa u njemu piše 16 + 40 + 16 = 72.

Broj petlji mijenja se pri izvođenju, bez ponovnog treninga, a zadane su 2. To je **elastično računanje** (elastic compute): iste težine, a više ili manje računanja po tokenu, prema tome što ti treba. Kontekst ide do 256K, a način KV cachea koji pamti samo zadnju petlju (last-loop) drži KV memoriju ravnom. Model je prednaučen u NVFP4 (poglavlje 18) i radi na engleskom.

Istraživački prethodnik (arXiv 2311.12424) daje važnu ogradu: petlje nakon trenirane granice brzo divergiraju. Više petlji zato ne znači automatski bolji odgovor. Autor Dory nije pokretao, a koliko se ta ograda na nju odnosi, nije provjereno. Benchmarke koje objavi proizvođač čitaj kao njegovo vlastito mjerenje, na tuđem skupu i jeziku te u tuđim uvjetima.

Što mehaničar iz toga uzima:

- **Račun se mijenja, a metoda ne.** Veličina datoteke opet ne govori sve, kao kod MoE-a u poglavlju 6. Uz zadane 2 petlje token prolazi 8 + 2 × 20 + 8 = 56 blokova, pa granicu brzine iz poglavlja 8 računaš prema onome što se po tokenu stvarno pročita. KV memoriju provjeri u logu.
- **Broj petlji je nova postavka,** kao razina kvantizacije. Za svaku vrijednost koju planiraš koristiti ponovi zlatni skup i p95.
- **Hrvatski testiraš sam,** isto kao kod svakog modela iz poglavlja 9.

## Kako dalje

Alati stare brže od ove knjige. Mjerenja su s llama.cpp b12110 i Pythona 3.14, a činjenice su stanje u studenom 2026. Kad nešto prestane raditi, usporedi inačice, pa pročitaj bilješke uz izdanje alata. Računica memorije, zlatni skup i ponovno mjerenje ostaju korisni i kad se imena promijene.

Podatke drži svježima na isti način kao model:

- Uz svaki broj zapiši stroj, alat, inačicu i datum. Broj bez toga ne vrijedi.
- Skripte iz `prilozi/` ponovno pokreni na svom stroju, a tablice ove knjige zamijeni svojima.
- Cijene, licence i pravne rokove provjeri iz izvora na dan odluke jer se mijenjaju bez upozorenja.
- Rang-liste koristi samo za popis kandidata.

Najbrže učiš na vlastitom poslu. Uzmi jedan stvarni zadatak, označi 40 primjera i izmjeri jedan model. Za novi model najprije čitaj karticu modela i `config.json`, pa ga pusti kroz taj skup. Za ono što ovdje namjerno izostaje, poput propagacije unatrag i PyTorcha, početna točka je literatura u dodatku C.

::: {.vjezba}
**Vježba: tvoja tablica stanja** `samo čitanje` · 30 min

Za jedan svoj posao napravi tablicu iz odjeljka "Gdje Kvaka stvarno stoji": cilj, granica, najbolje izmjereno, stanje. U praznu ćeliju upiši "nije izmjereno", a ispod napiši tri sljedeća koraka od najjeftinijeg. Ako ne možeš napisati granicu, kreni od nje.
:::

## Sažetak

Kvaka prolazi cijeli put od cilja i zlatnog skupa do posluživanja, a najbolji rezultat ostaje Gemma 4 E2B sa shemom: 74,4 % prema traženih 90 %, bez adaptera. Latencija ne ulazi u 5 s ni na stvarnom zadatku (p95 6,7 s) ni uz četiri klijenta (13,36 s), a granicu od 150 EUR prolaze samo API i povremeni najam, i to na izmišljenim ulazima i bez izmjerene točnosti. Sljedeći koraci su bolja poruka, drugi modeli, stvarni podaci, QLoRA na većoj bazi i jači stroj, a ako ni oni ne uspiju, ostaju niži cilj, ljudska provjera ili odustajanje. Pravila, tablica kvarova i kontrolna lista vrijede i za tvoj posao, uz napomenu da licencu i AI Act provjeravaš iz izvora prije oslanjanja. Modeli s petljama poput Dory mijenjaju račun, ali ih čitaš i mjeriš istim alatima, a svaki broj iz ove knjige zamijeni svojim.
