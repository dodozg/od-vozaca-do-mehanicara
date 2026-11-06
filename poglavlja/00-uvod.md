# Kako čitati ovu knjižicu

Ova je knjižica za osobu koja svakodnevno radi s ChatGPT-om, Claudeom ili Geminijem, zna pisati promptove, a nikad nije pokrenula model. Ovdje ne učiš PyTorch i ne izvodiš backpropagation.

## Redoslijed

Jezgra su poglavlja 1 do 16 i čitaju se redom jer se svako oslanja na prethodna. Poglavlja 17 i 18 izborna su. Poglavlje 19 prolazi cijeli put na istom primjeru i služi kao podsjetnik. Na kraju su rječnik, šalabahter i izvori.

## Oznake

Svaka vježba u okviru ima oznaku i procjenu RAM-a, diska i vremena:

- `CPU`: radi na običnom računalu.
- `najam GPU-a`: traži grafičku karticu koju možeš unajmiti na sat.
- `samo čitanje`: računaš ili čitaš, bez pokretanja modela.

Okvir "Simptom → uzrok" popisuje česte kvarove i popravke. Okvir **Nije pokrenuto** stoji iza svakog koda koji autori nisu stvarno izveli. Takav kod shvati kao polazište i provjeri ga. "Autor" u tim okvirima znači onoga tko je izvodio vježbe.

## Odakle su brojke

Mjereno je na slabom laptopu: Intel i5-10210U (četiri od osam dretvi), 16 GB RAM-a, bez GPU-a, Windows 11 Pro, llama.cpp b12110, Python 3.14, transformers 5.22.1, peft 0.21.2. Brzine su se na tom stroju u istom danu razlikovale i do dva puta. Tvoje će biti drukčije, zato izmjeri svoje.

Knjiga je datirana studenim 2026. Alati, licence i cijene brzo stare. Kad se nešto ne slaže, usporedi inačice i pogledaj izvor.

## Prilozi

Mapa `prilozi/` sadrži sintetički skup Kvake d.o.o. (240 zapisnika za trening i 60 za validaciju), zlatni skup od 40 primjera, shemu, kratki priručnik za RAG i skripte vježbi s uputama. Kvaka d.o.o. izmišljena je tvrtka.

## Kako je knjiga nastala

Polazište je kraći priručnik Domagoja Zoričića, *Praktični priručnik za inženjering LLM težina*. Tekst je napisan s Claudeom i njegovim agentima, a ti su agenti vježbe stvarno pokrenuli na opisanom laptopu. Greške su moguće i unatoč provjeri, pa važne tvrdnje usporedi s izvorima iz dodatka C.
