# L3: tokeni. Isti odlomak na hrvatskom i engleskom pod više tokenizatora te raspad pojedinih riječi.
# Pokretanje: python l3_tokeni.py MAPA_MODELA_SMOLLM3 MAPA_MODELA_SMOLLM2 GGUF1 GGUF2 ... (GGUF se broji kroz llama-tokenize)
import sys, os, subprocess, json, tempfile
from transformers import AutoTokenizer
HR = ("Kada perilica rublja stane usred programa i u bubnju ostane voda, prvo treba isključiti uređaj iz struje i zatvoriti dovod vode. "
      "Zatim ispod uređaja stavite plitku posudu, otvorite poklopac u donjem desnom kutu i polako odvrnite filtar pumpe. U filtru se najčešće nađu kovanice, "
      "dugmad, kopče i vlakna, koji sprečavaju izbacivanje vode. Ako je filtar čist, provjerite je li odvodno crijevo presavijeno ili začepljeno. "
      "Ako ni tada voda ne izlazi, a pumpa se ne čuje ili samo tiho bruji, vjerojatno je pumpa neispravna i treba je zamijeniti. Popravak obično traje oko sat vremena, "
      "a serviser će prije zamjene izmjeriti otpor namota. Stranci treba reći da uređaj do dolaska servisera ne pokreće, jer bi voda mogla iscuriti na pod. "
      "U zapisnik se upisuju model, serijski broj, opis kvara, zamijenjeni dio i vrijeme rada, kako bi jamstvo vrijedilo dvije godine od dana popravka.")
EN = ("When a washing machine stops in the middle of a programme and water remains in the drum, first unplug the appliance and close the water supply. "
      "Then place a shallow container under the machine, open the cover in the lower right corner and slowly unscrew the pump filter. The filter most often contains coins, "
      "buttons, clips and fibres, which prevent the water from draining. If the filter is clean, check whether the drain hose is kinked or blocked. "
      "If water still does not come out, and the pump cannot be heard or only hums quietly, the pump is probably faulty and has to be replaced. The repair usually takes about an hour, "
      "and the technician will measure the winding resistance before the replacement. Tell the customer not to start the appliance until the technician arrives, because water could leak onto the floor. "
      "The model, serial number, fault description, replaced part and working time are entered in the report, so that the warranty is valid for two years from the date of repair.")
RIJECI = ["popravak", "perilica", "najnepredvidljivijih", "čišćenje", "cistenje", "kompresor", "washing", "unpredictable", "Zagreb", "2026", "4,89"]
print("rijeci HR", len(HR.split()), "znakova", len(HR)); print("rijeci EN", len(EN.split()), "znakova", len(EN))
print("HR:", HR); print("EN:", EN)
tok = {"SmolLM3-3B": AutoTokenizer.from_pretrained(sys.argv[1]), "SmolLM2-135M": AutoTokenizer.from_pretrained(sys.argv[2])}
for ime, t in tok.items():
    h, e = t(HR, add_special_tokens=False).input_ids, t(EN, add_special_tokens=False).input_ids
    print(f"\n== {ime}: vocab {t.vocab_size}, ukupno s posebnima {len(t)}  HR {len(h)} tokena, EN {len(e)} tokena, omjer HR/EN {len(h)/len(e):.2f}, token/rijec HR {len(h)/len(HR.split()):.2f} EN {len(e)/len(EN.split()):.2f}")
    for r in RIJECI:
        ids = t(" " + r, add_special_tokens=False).input_ids if r[0].isalpha() else t(r, add_special_tokens=False).input_ids
        print(f"  {r:<24} {len(ids):>2}  {[t.decode([i]) for i in ids]}")
    print("  posebni:", t.special_tokens_map)
    dod = {k: v.content for k, v in t.added_tokens_decoder.items()}
    print("  added_tokens_decoder broj:", len(dod), "prvih 10:", list(dod.items())[:10], "zadnjih 6:", list(dod.items())[-6:])
# GGUF modeli imaju vlastiti tokenizator ugrađen u datoteku
for g in sys.argv[3:]:
    ime = os.path.basename(g)
    print(f"\n== {ime} (llama-tokenize)")
    for jezik, tekst in (("HR", HR), ("EN", EN)):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f: f.write(tekst)
        r = subprocess.run([os.path.abspath("llama/llama-tokenize.exe"), "-m", g, "-f", f.name, "--ids", "--no-bos", "--log-disable"], capture_output=True)
        os.unlink(f.name)
        ids = json.loads(r.stdout.decode("utf-8", "replace").strip().splitlines()[-1])
        print(f"  {jezik} {len(ids)} tokena")
        if jezik == "HR": nh = len(ids)
    print(f"  omjer HR/EN {nh/len(ids):.2f}")
    for r_ in RIJECI:
        r = subprocess.run([os.path.abspath("llama/llama-tokenize.exe"), "-m", g, "-p", " "+r_, "--no-bos", "--log-disable"], capture_output=True)
        izlaz = r.stdout.decode("utf-8", "replace").strip().splitlines()
        print(f"  {r_:<24} {len(izlaz):>2}  {[x.split('->')[1].strip() if '->' in x else x for x in izlaz]}")
